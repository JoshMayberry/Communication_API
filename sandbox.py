# import subprocess
# info = subprocess.STARTUPINFO()
# info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
# info.wShowWindow = subprocess.SW_HIDE


# #Ping the address
# output = subprocess.Popen(['start', '\\\\dmte6\\MyWPData\\Sales_Orders\\20014'], stdout=subprocess.PIPE, startupinfo=info).communicate()[0]
# print(output)
# print(output.decode("utf-8"))

import os
os.startfile("\\\\dmte6\\MyWPData\\Sales_Orders")