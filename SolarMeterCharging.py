from serial import Serial
import time
import re
from Lib.lcd import lcddriver
import mysql.connector


# Load the driver and set it to "display"
# If you use something from the driver library use the "display." prefix first
LcdCursor = lcddriver.lcd()

ser = Serial('/dev/ttyACM0', baudrate = 9600, timeout = 1)
time.sleep(3)

def GetSubStringByChar(Data = dict()):
    StartPos = Data['Str'].find(Data['Before'])
    TmpStr = Data['Str'][(StartPos+len(Data['Before'])):]
    EndPos = TmpStr.find(Data['After'])
    FinalString = TmpStr[:EndPos]
    return FinalString

def ConvertSecToTime(GivenSeconds):
    year = GivenSeconds // (12 * 30 * 24 * 3600)
    GivenSeconds = GivenSeconds % (12 * 30 * 24 * 3600)

    month = GivenSeconds // (30 * 24 * 3600)
    GivenSeconds = GivenSeconds % (30 * 24 * 3600)

    day = GivenSeconds // (24 * 3600)
    GivenSeconds = GivenSeconds % (24 * 3600)

    hour = GivenSeconds // 3600
    GivenSeconds %= 3600

    minute = GivenSeconds // 60
    GivenSeconds %= 60

    second = int(GivenSeconds)

    millisecond = int(str(round((GivenSeconds - int(GivenSeconds)),2))[2:])

    if(year != 0):
        return f'''{year} year - {month} month - {day} day - {hour} hour : {minute} minute : {second} second : {millisecond} millisecond'''
    elif(year == 0 and month != 0):
        return f'''{month} month - {day} day - {hour} hour : {minute} minute : {second} second : {millisecond} millisecond'''
    elif(year == 0 and month == 0 and day != 0):
        return f'''{day} day - {hour} hour : {minute} minute : {second} second : {millisecond} millisecond'''
    elif(year == 0 and month == 0 and day == 0 and hour != 0):
        return f'''{hour} hour : {minute} minute : {second} second : {millisecond} millisecond'''
    elif(year == 0 and month == 0 and day == 0 and hour == 0 and minute != 0):
        return f'''{minute} minute : {second} second : {millisecond} millisecond'''
    elif(year == 0 and month == 0 and day == 0 and hour == 0 and minute == 0 and second != 0):
        return f'''{second} second : {millisecond} millisecond'''
    else:
        return f'''{millisecond} millisecond'''


#How to install mysql server
#1. sudo apt install mariadb-server
#2. sudo mysql_secure_installation
#3. mysql -u solar_meter(username) -p

# Database connection with mysql#
conn = mysql.connector.connect(host='localhost',user='solar_meter',password='solar_meter_pass',database="solar_meter")
#Creating a cursor object using the cursor() method
connCursor = conn.cursor()


i = 0
while (i < 20):
    ser.readline()
    i = i+1
while (i < 20):
    ser.readline().decode('ascii')
    i = i+1

IsRunning = 0
while True:
    if(IsRunning != 0):
        i = 0
        while(i < 20):
            time.sleep(1)
            i = i+1
    else:
        IsRunning = 1
        
    i = 0
    TmpBatteryVoltSensor = 0.0
    while (i < 8):
        try:
            AurdinoSerialRead = ser.readline().decode('ascii')
            BatteryVoltSensor = float(GetSubStringByChar({'Str':AurdinoSerialRead,'Before':'||VoltMeterSensor|','After':'||'}))
            if(BatteryVoltSensor < 0 or BatteryVoltSensor > 15):
                LcdCursor.lcd_display_string(f"Error: Invalid volt",1)
                print('Warning : Warning : Invalid volage found')
                continue
            TmpBatteryVoltSensor = TmpBatteryVoltSensor+BatteryVoltSensor
        except:
            LcdCursor.lcd_display_string(f"Error:can't read serial",1)
            print('Warning : can not able to read aurdino serial data')
            continue
        i = i+1
    BatteryVoltSensor = round(TmpBatteryVoltSensor/8, 2)
    if(BatteryVoltSensor < 0 or BatteryVoltSensor > 15):
            LcdCursor.lcd_display_string(f"Warning : Invalid voltage found",1)
            print('Warning : Invalid volage found')
            continue

    CurrentSenosr = 3.20
    CurrentTime = time.time()
    if(type(BatteryVoltSensor) != float or type(CurrentSenosr) != float  or type(CurrentTime) != float):
        LcdCursor.lcd_display_string(f"Warning : Invalid data found to insert",1)
        print('Warning : Invalid data found to insert')
        continue


    #>>>>>>>>>>>>>>>>> Insert Solar Charging Data In Database <<<<<<<<<<<<<<<<<<<<#

    try:
        # Preparing SQL queries to INSERT a record into the database.
        sql = "INSERT INTO solar_meter_charging (CurrentTime, BatteryVolt, CurrentAmp) VALUES (%s, %s, %s)"
        val = (CurrentTime,BatteryVoltSensor,CurrentSenosr)
        connCursor.execute(sql, val)
        conn.commit()
        CurrentLocalTime = time.localtime(CurrentTime)
        print(f'Success : Solar meter Charging data successfully inserted at {CurrentLocalTime.tm_hour}:{CurrentLocalTime.tm_min}:{CurrentLocalTime.tm_sec}, {CurrentLocalTime.tm_mday} - {CurrentLocalTime.tm_mon} - {CurrentLocalTime.tm_year}')
        #LcdCursor.lcd_display_string(f'Success : Solar meter Charging data successfully inserted at {CurrentLocalTime.tm_hour}:{CurrentLocalTime.tm_min}:{CurrentLocalTime.tm_sec}, {CurrentLocalTime.tm_mday} - {CurrentLocalTime.tm_mon} - {CurrentLocalTime.tm_year}', 1)
    except:
        print('Warning : Solar meter Charging data can not inserted')
        LcdCursor.lcd_display_string(f'''Warning : Solar meter Charging data can not inserted''', 1)
        continue


    #>>>>>>>>>>>>>>>>>>> Get Data From Database And Done calculations <<<<<<<<<<<<<<<<<<<#

    #>>>>>>>>>> Calulations for Solar Charging Between Two Time <<<<<<<<<<#
    # upto 60 sec before from cureent time
    #DataGetUptoLastTime = time.time() - 60

    #try:
        # Preparing SQL queries to fetch data from database
    #    sql = f'''select BatteryVolt as BVolt, CurrentTime as CTime from solar_meter_charging WHERE CurrentTime >= {DataGetUptoLastTime} ORDER BY CurrentTime ASC LIMIT 1'''
    #    connCursor.execute(sql)
    #    FromStartDateChargingData = connCursor.fetchall()
    #    if(len(FromStartDateChargingData) != 0):
    #        FromStartDateChargingData = FromStartDateChargingData[0]
    #        FromStartDateChargingDataTime = float(FromStartDateChargingData[1])
    #        FromStartDateChargingDataVolt = float(FromStartDateChargingData[0])
    #        LocalTimeFromStartDateChargingDataTime = time.localtime(FromStartDateChargingDataTime)

            # Preparing SQL queries to fetch data from database
    #        sql = f'''select BatteryVolt as BVolt, CurrentTime as CTime from solar_meter_charging WHERE CurrentTime <= {CurrentTime} ORDER BY CurrentTime DESC LIMIT 1'''
    #        connCursor.execute(sql)
    #        FromEndDateChargingData = connCursor.fetchall()
    #        if(len(FromEndDateChargingData) == 0):
    #            LcdCursor.lcd_display_string(f'''Notice : Currently we don't have battery volt data from given time''', 2)
    #            print("Notice : Currently we don't have battery volt data from given time")
    #        else:
    #            FromEndDateChargingData = FromEndDateChargingData[0]
    #            FromEndDateChargingDataTime = float(FromEndDateChargingData[1])
    #            FromEndDateChargingDataVolt = float(FromEndDateChargingData[0])
    #            ChargingDataBetweenTwoTime = FromEndDateChargingDataVolt - FromStartDateChargingDataVolt
    #            LocalTimeFromEndDateChargingData = time.localtime(FromEndDateChargingDataTime)
    #            LcdCursor.lcd_display_string(f'''Charging volt between {LocalTimeFromStartDateChargingDataTime.tm_hour}:{LocalTimeFromStartDateChargingDataTime.tm_min}:{LocalTimeFromStartDateChargingDataTime.tm_sec}, {LocalTimeFromStartDateChargingDataTime.tm_mday} - {LocalTimeFromStartDateChargingDataTime.tm_mon} - {LocalTimeFromStartDateChargingDataTime.tm_year} to {LocalTimeFromEndDateChargingData.tm_hour}:{LocalTimeFromEndDateChargingData.tm_min}:{LocalTimeFromEndDateChargingData.tm_sec}, {LocalTimeFromEndDateChargingData.tm_mday} - {LocalTimeFromEndDateChargingData.tm_mon} - {LocalTimeFromEndDateChargingData.tm_year} : {ChargingDataBetweenTwoTime} volts''', 2)
    #            print(f"Charging volt between {LocalTimeFromStartDateChargingDataTime.tm_hour}:{LocalTimeFromStartDateChargingDataTime.tm_min}:{LocalTimeFromStartDateChargingDataTime.tm_sec}, {LocalTimeFromStartDateChargingDataTime.tm_mday} - {LocalTimeFromStartDateChargingDataTime.tm_mon} - {LocalTimeFromStartDateChargingDataTime.tm_year} to {LocalTimeFromEndDateChargingData.tm_hour}:{LocalTimeFromEndDateChargingData.tm_min}:{LocalTimeFromEndDateChargingData.tm_sec}, {LocalTimeFromEndDateChargingData.tm_mday} - {LocalTimeFromEndDateChargingData.tm_mon} - {LocalTimeFromEndDateChargingData.tm_year} : {ChargingDataBetweenTwoTime} volts")
    #    else:
    #        LcdCursor.lcd_display_string(f'''Notice : Currently we don't have battery volt data from given time''', 2)
    #        print(f"Notice : Currently we don't have battery volt data from given time")

    #except:
    #    LcdCursor.lcd_display_string(f'''Notice : We can not able to read data from Solar Meter Charging [ChargingDataBetweenTwoTime]''', 2)
    #    print("Notice : We can not able to read data from Solar Meter Charging [ChargingDataBetweenTwoTime]")






    #>>>>>>>>>> Calulations for Time charging from given to given volts <<<<<<<<<<#
    # time check from <=11.2 volts
    FromChargingVoltStart = 11.2
    # time check until >=14.0 volts
    FromChargingVoltEnd = 14.0

    try:
        # Preparing SQL queries to fetch data from database
        sql = f'''select CurrentTime As CTime, BatteryVolt As BVolt from solar_meter_charging WHERE BatteryVolt <= {FromChargingVoltStart} ORDER BY CurrentTime DESC LIMIT 1'''
        connCursor.execute(sql)
        FromStartChargingVoltData = connCursor.fetchall()
        if(len(FromStartChargingVoltData) != 0):
            FromStartChargingVoltData = FromStartChargingVoltData[0]
            FromStartChargingVoltDataTime = float(FromStartChargingVoltData[0])
            LocalTimeFromStartChargingVoltDataTime = time.localtime(FromStartChargingVoltDataTime)
            FromStartChargingVoltDataBatteryVolt = float(FromStartChargingVoltData[1])

            # Preparing SQL queries to fetch data from database
            sql = f'''select CurrentTime As CTime, BatteryVolt As BVolt from solar_meter_charging WHERE BatteryVolt >= {FromChargingVoltEnd} ORDER BY CurrentTime ASC LIMIT 1'''
            connCursor.execute(sql)
            FromEndChargingVoltData = connCursor.fetchall()
            if(len(FromEndChargingVoltData) == 0):
                LcdCursor.lcd_display_string(f'''Charging {FromStartChargingVoltDataBatteryVolt} : {BatteryVoltSensor} volt''', 3)
                print(f'''Battery start charging from {FromStartChargingVoltDataBatteryVolt} volt at {LocalTimeFromStartChargingVoltDataTime.tm_hour}:{LocalTimeFromStartChargingVoltDataTime.tm_min}:{LocalTimeFromStartChargingVoltDataTime.tm_sec}, {LocalTimeFromStartChargingVoltDataTime.tm_mday} - {LocalTimeFromStartChargingVoltDataTime.tm_mon} - {LocalTimeFromStartChargingVoltDataTime.tm_year} time and Current voltage is {BatteryVoltSensor} volt''')
            else:
                FromEndChargingVoltData = FromEndChargingVoltData[0]
                FromEndChargingVoltDataTime = float(FromEndChargingVoltData[0])
                LocalTimeFromEndChargingVoltDataTime = time.localtime(FromEndChargingVoltDataTime)
                FromEndChargingVoltDataBatteryVolt = float(FromEndChargingVoltData[1])
                if(len(FromEndChargingVoltData) != 2):
                    LcdCursor.lcd_display_string(f'''Notice : Currently we don't have battery volt data from given time''', 3)
                    print("Notice 1 : Currently we don't have battery volt data from given time")
                else:
                    print(FromStartChargingVoltData)
                    print(FromEndChargingVoltData)
                    ChargingTimeBetweenTwoGivenVolt = FromEndChargingVoltDataBatteryVolt - FromStartChargingVoltDataBatteryVolt
                    ChargingTimeBetweenTwoGivenVoltTimeDiffInSec = FromEndChargingVoltDataTime - FromStartChargingVoltDataTime
                    ChargingTimeBetweenTwoGivenVoltTimeDiffInHMS = ConvertSecToTime(ChargingTimeBetweenTwoGivenVoltTimeDiffInSec)
                    LcdCursor.lcd_display_string(f'''Charging from {LocalTimeFromStartChargingVoltDataTime.tm_hour}:{LocalTimeFromStartChargingVoltDataTime.tm_min}:{LocalTimeFromStartChargingVoltDataTime.tm_sec}, {LocalTimeFromStartChargingVoltDataTime.tm_mday} - {LocalTimeFromStartChargingVoltDataTime.tm_mon} - {LocalTimeFromStartChargingVoltDataTime.tm_year} to {LocalTimeFromEndChargingVoltDataTime.tm_hour}:{LocalTimeFromEndChargingVoltDataTime.tm_min}:{LocalTimeFromEndChargingVoltDataTime.tm_sec}, {LocalTimeFromEndChargingVoltDataTime.tm_mday} - {LocalTimeFromEndChargingVoltDataTime.tm_mon} - {LocalTimeFromEndChargingVoltDataTime.tm_year} time and from {FromStartChargingVoltDataBatteryVolt} to {FromEndChargingVoltDataBatteryVolt} volt, it take {ChargingTimeBetweenTwoGivenVoltTimeDiffInHMS} time''', 3)
                    print(f"Charging from {LocalTimeFromStartChargingVoltDataTime.tm_hour}:{LocalTimeFromStartChargingVoltDataTime.tm_min}:{LocalTimeFromStartChargingVoltDataTime.tm_sec}, {LocalTimeFromStartChargingVoltDataTime.tm_mday} - {LocalTimeFromStartChargingVoltDataTime.tm_mon} - {LocalTimeFromStartChargingVoltDataTime.tm_year} to {LocalTimeFromEndChargingVoltDataTime.tm_hour}:{LocalTimeFromEndChargingVoltDataTime.tm_min}:{LocalTimeFromEndChargingVoltDataTime.tm_sec}, {LocalTimeFromEndChargingVoltDataTime.tm_mday} - {LocalTimeFromEndChargingVoltDataTime.tm_mon} - {LocalTimeFromEndChargingVoltDataTime.tm_year} time and from {FromStartChargingVoltDataBatteryVolt} to {FromEndChargingVoltDataBatteryVolt} volt, it take {ChargingTimeBetweenTwoGivenVoltTimeDiffInHMS} time")
                    time.sleep(15)
        else:
            LcdCursor.lcd_display_string(f'''Notice : Currently we don't have battery volt data from given time''', 3)
            print(f"Notice 2 : Currently we don't have battery volt data from given time")
            time.sleep(50)
    except:
        LcdCursor.lcd_display_string(f'''Notice : We can not able to read data from Solar Meter Charging [ChargingTimeBetweenTwoVolts]''', 3)
        print("Notice 3 : We can not able to read data from Solar Meter Charging [ChargingTimeBetweenTwoVolts]")