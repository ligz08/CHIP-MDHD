# HRS Equipment

## List of Available Equipment

### Hydrogen Compressor
Implementation class: `HydrogenCompressor`

Theoritical power required (kW) = B25="20 bar supply" ?
    [Mean Compressibility Factor for Main Compressor] * ([thruput_kg/min]/60/2.0158) * [R_u] * [Maximum hydrogen temperature at the station (K)] * [Number of stages (2)] * ([C_p/C_v ratio]/([C_p/C_v ratio]-1))*(([Main Compressor Discharge Pressure (atm)]/[Pressure of Hydrogen Delivered to Refueling Station (atm)])^(([C_p/C_v ratio]-1)/ ( [Number of stages (2)] * [C_p/C_v ratio]))-1)
    :
    [Mean Compressibility Factor for Main Compressor] * ([thruput_kg/min]/60/2.0158) * [R_u] * [Maximum hydrogen temperature at the station (K)] * [Number of stages (2)] * ([C_p/C_v ratio]/([C_p/C_v ratio]-1))*(([Main Compressor Discharge Pressure (atm)]/[Minimum Pressure in the Tube Trailer (atm)])^(([C_p/C_v ratio]-1)/ ( [Number of stages (2)] * [C_p/C_v ratio]))-1)))

### Hydrogen Storage
Implementation class: `HydrogenStorage`



### Hydrogen Dispenser


### Refrigerator


### Electrical Controller


### Electrolyzer


### SteamMethaneReformer

