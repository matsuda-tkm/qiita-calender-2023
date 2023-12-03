import numpy as np

# 世界測地系(GRS80)
A = 6378137.0
F = 1/298.257222101
B = A*(1-F)

# 日本測地系(Bessel)
# A = 6377397.155
# F = 1/299.152813
# B = A*(1-F)

# Google Maps
# A = 6371008
# B = A
# F = (A-B)/A

def dist(p1, p2):
    global A, B, F
    
    # 緯度経度をラジアンに変換
    lat1 = np.radians(p1[0])
    lon1 = np.radians(p1[1])
    lat2 = np.radians(p2[0])
    lon2 = np.radians(p2[1])

    # 化成緯度に変換
    phi1 = np.arctan2(B * np.tan(lat1), A)
    phi2 = np.arctan2(B * np.tan(lat2), A)

    # 球面上の距離
    X = np.arccos(np.sin(phi1) * np.sin(phi2) + np.cos(phi1) * np.cos(phi2) * np.cos(lon2 - lon1))

    # Lambert-Andoyer補正
    drho = F/8 * ((np.sin(X) - X) * (np.sin(phi1) + np.sin(phi2))**2 / np.cos(X/2)**2 - (np.sin(X) + X) * (np.sin(phi1) - np.sin(phi2))**2 / np.sin(X/2)**2)

    # 距離
    rho = A * (X + drho)

    return rho

if __name__ == '__main__':
    p1 = (43+3/60+52/3600, 141+20/60+49/3600)  # 北海道庁
    p2 = (26+12/60+45/3600, 127+40/60+51/3600) # 沖縄県庁
    print(dist(p1,p2))

# 都道府県庁の緯度経度は https://www.gsi.go.jp/common/000230936.pdf を参考