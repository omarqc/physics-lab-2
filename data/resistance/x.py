import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv("05_06_resistance_IV_Run5.csv")
df2 = pd.read_csv("05_06_resistance_IV_Run6.csv")
df3 = pd.read_csv("05_06_resistance_IV_Run7.csv")

t = "Time"
i = "Current"
v = "Voltage"

fig, ax = plt.subplots()

plt.plot(df1[t],df1[v]*1e9)
plt.plot(df2[t],df2[v]*1e9)
plt.plot(df3[t],df3[v]*1e9)

plt.xlabel("Time / s", fontsize=25)
plt.ylabel(r"Voltage / nV", fontsize=25)

plt.xlim(0,130)

plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.grid()
plt.show()
