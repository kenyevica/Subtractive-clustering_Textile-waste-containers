def give_GPS(df_allcity,df_centers):
    df_centers["y_lat"] = 0
    df_centers["x_lon"] = 0
    for i in df_centers['Town']:
        df_centers["y_lat"][df_centers['Town'] == i] = df_allcity[df_allcity['Town'] == i]["y_lat"].iloc[0]
        df_centers["x_lon"][df_centers['Town'] == i] = df_allcity[df_allcity['Town'] == i]["x_lon"].iloc[0]
    return df_centers