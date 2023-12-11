import argparse
import os
import datetime
import asyncio
import struct
from tqdm import tqdm
import bleak

UUID = {
    'latestData': '3001',
    'latestPage': '3002',
    'requestPage': '3003',
    'responseFlag': '3004',
    'responseData': '3005',
    'eventFlag': '3006',
    'measurementInterval': '3011'
}

def unix_to_jst(unix_time, return_str=False):
    '''Convert UNIX time to JST time'''
    jst_time = datetime.datetime.fromtimestamp(unix_time)
    jst_time += datetime.timedelta(hours=9)
    if return_str:
        return jst_time.strftime("%Y/%m/%d %H:%M:%S")
    else:
        return jst_time

async def connect(device_name, loop, datefrom, output):
    datefrom = datetime.datetime.strptime(datefrom, '%Y/%m/%d %H:%M:%S')
    break_flag = False

    # Discover devices
    devices = await bleak.BleakScanner.discover()
    device = next((d for d in devices if d.name == device_name), None)
    if not device:
        raise bleak.exc.BleakDeviceNotFoundError(f'Device "{device_name}" not found.')

    # Connect to the device
    async with bleak.BleakClient(device, loop=loop) as client:
        print('Connected!')

        # Get the latest page
        data = await client.read_gatt_char(f'0c4c{UUID["latestPage"]}-7700-46f4-aa96-d5e974e32a54')
        (latest_page_time, interval, latest_page, latest_row) = struct.unpack('<IHHB', data)
        latest_page_time = unix_to_jst(latest_page_time + interval * latest_row)
        print(f'Latest page: {latest_page}, Latest row: {latest_row}, Latest page time: {latest_page_time}')

        # Get the page data
        for page in reversed(range(latest_page + 1)):
            # Request the page
            set_value = struct.pack('<HB', page, latest_row if page == latest_page else 12)
            await client.write_gatt_char(f'0c4c{UUID["requestPage"]}-7700-46f4-aa96-d5e974e32a54', set_value)
            # Check for updates
            flag, retry = 0, 0
            while flag != 1:
                response_flag = await client.read_gatt_char(f'0c4c{UUID["responseFlag"]}-7700-46f4-aa96-d5e974e32a54')
                (flag, start_time) = struct.unpack('<BI', response_flag)
                retry += 1
                if retry > 1:
                    print(f'Retrying request page (Page:{page}, Status:{flag})')
            # Get the page data
            for row in reversed(range(latest_row+1 if page == latest_page else 12+1)):
                if unix_to_jst(start_time + interval * row) < datefrom:  # Do not retrieve data before the specified date and time
                    break_flag = True
                    break
                page_value = await client.read_gatt_char(f'0c4c{UUID["responseData"]}-7700-46f4-aa96-d5e974e32a54')
                (row, temp, hum, light, uv, press, noise, discom, heat, batt) = struct.unpack('<BhhhhhhhhH', page_value)
                time = unix_to_jst(start_time + interval * row, return_str=True)
                temp /= 100
                hum /= 100
                uv /= 100
                press /= 10
                noise /= 100
                discom /= 100
                heat /= 100
                batt /= 1000
                # Write to file
                mode = 'a' if os.path.exists(output) else 'w'
                with open(output, mode) as f:
                    f.write(f'{time},{temp},{hum},{light},{uv},{press},{noise},{discom},{heat},{batt}\n')
            if break_flag:
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--datefrom', type=str, help='Date from(YYYY/MM/DD HH:MM:SS)')
    parser.add_argument('-o', '--output', type=str, help='Output file name')
    args = parser.parse_args()

    assert args.datefrom, 'option "--datefrom" is required. Please specify the date and time from which you want to retrieve the data.'
    assert args.output, 'option "--output" is required. Please specify the output file name.'
    
    if os.path.exists(args.output):
        input(f'WARNING : "{args.output}" already exists. The data will be appended to the file. Press Enter to continue (Ctrl+C to cancel).')

    while True:
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(connect('Env', loop, args.datefrom, args.output))
            break
        except asyncio.exceptions.TimeoutError:
            print('Timeout. Retrying...')
        except bleak.exc.BleakDeviceNotFoundError:
            print('Device not found. Retrying...')
