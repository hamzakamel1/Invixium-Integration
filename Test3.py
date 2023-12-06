import os
import datetime
import clr
import logging
import struct

# Add references to the required DLL files
clr.AddReference('C:/Users/hamza/OneDrive/Desktop/Test2/IXMDemo.Common.dll')
clr.AddReference('C:/Users/hamza/OneDrive/Desktop/Test2/IXMSoft.Business.Managers.dll')
clr.AddReference('C:/Users/hamza/OneDrive/Desktop/Test2/IXMSoft.Business.SDK.dll')
clr.AddReference('C:/Users/hamza/OneDrive/Desktop/Test2/IXMSoft.Common.Models.dll')
clr.AddReference('C:/Users/hamza/OneDrive/Desktop/Test2/IXMSoft.Data.DataAccess.dll')

# Import the necessary functions and classes from the DLLs using ctypes

# from IXMSoft.Common.Models import Device
from IXMDemo.Common import Device
from IXMSoft.Business.SDK import *
from IXMSoft.Data.DataAccess import *
from IXMSoft.Business.SDK.Data import DeviceConnectionType, TransactionLogEventType
from IXMSoft.Business.SDK import NetworkConnection, TransactionLogManager
from IXMSoft.Business.SDK.Commands import ITransactionLogArgs

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_full_path(path):
    app_folder_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(app_folder_path, path)
    return path

def check_device_status(device):
    if device.IPaddress and device.Port:
        try:
            response = os.system(f"ping {device.IPaddress} -n 1")
            if response == 0:
                return True
        except Exception as ex:
            logging.error(f"Error checking device status: {ex}")
    return False

def get_transaction_logs(conn, start_date, end_date):
    transaction_logs = []
    log_count = 0  # Initialize log count

    try:
        logdata = TransactionLogManager(conn)
        TransactionLogArguments = ITransactionLogArgs()  # Create an instance of ITransactionLogArgs
        TransactionLogArguments.StartDate = start_date
        TransactionLogArguments.EndDate = end_date

        device_info_manager = DeviceInfoManager(conn)

        AllLogCounter = logdata.GetAllDateWiseTransactionLogCount(TransactionLogArguments)  # Get log count

        if AllLogCounter > 0:
            for i in range(0, AllLogCounter, 100):
                TransactionLogArguments.StartCounter = i
                TransactionLogArguments.EndCounter = i + 100
                datawise = get_date_wise_transaction_log(conn, TransactionLogArguments)  # Correct argument format

                for item in datawise:
                    if item.EventType == TransactionLogEventType.Authentication:
                        std_log_data = employee_data(str(item.UserId), item.Date.ToShortDateString(), item.Time.ToString(), item.Event.ToString(), "")
                        if std_log_data:
                            transaction_logs.append(std_log_data)
                            log_count += 1  # Increment log count

    except Exception as ex:
        logging.error(f"Error getting transaction logs: {ex}")

    return transaction_logs, log_count  # Return both logs and log count

def employee_data(userid, date, time, event, access_schedule):
    data_row = {}
    data_row["UserRecordId"] = userid
    data_row["check_date"] = date
    data_row["check_time"] = time
    return data_row

def main():
    logs_folder = "logs"
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    file_name_date = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=1)

    date_path = "date.txt"
    logging.info("Check if date file exists.")
    date_path = get_full_path(date_path)
    if os.path.exists(date_path):
        logging.info("Date file found. Reading dates.")
        with open(date_path, 'r') as date_file:
            dates = date_file.readlines()
            for i, date in enumerate(dates):
                if i == 0:
                    start_date = datetime.datetime.strptime(date.strip(), "%Y-%m-%d %H:%M:%S")
                    logging.info(f"Start date set to: {start_date}")
                elif i == 1:
                    end_date = datetime.datetime.strptime(date.strip(), "%Y-%m-%d %H:%M:%S")
                    logging.info(f"End date set to: {end_date}")

    # Use the specified IP address and port
    device = Device()
    device.IPaddress = "192.168.200.143"
    device.Port = "9734"
    device.ConnectionType = DeviceConnectionType.Ethernet

    logging.info(f"Checking device status for IP: {device.IPaddress}")
    status = check_device_status(device)
    logging.info(f"Device status: {status}")
    if status:
        rows = []
        logging.info(f"Establishing a network connection to IP: {device.IPaddress}")
        conn = NetworkConnection(device)
        try:
            conn.OpenConnection()
            logging.info(f"Network connection established: {conn.OpenConnection()}")

            logging.info(f"Retrieving transaction logs for IP: {device.IPaddress} from {start_date} to {end_date}")
            rows, log_count = get_transaction_logs(conn, start_date, end_date)  # Update rows and log_count
            conn.CloseConnection()
            conn.Dispose()
        except Exception as ex:
            conn.CloseConnection()
            conn.Dispose()
            logging.error(f"Error during network communication: {ex}")

        # Print the count of logs
        logging.info(f"Total logs retrieved: {log_count}")

        log_path = f"{device.IPaddress}_{file_name_date}.txt"
        log_path = os.path.join(logs_folder, log_path)
        log_path = get_full_path(log_path)
        with open(log_path, 'w') as writer:
            for row in rows:
                data = f"{row['UserRecordId']};{row['check_date']};{row['check_time']}"
                writer.write(data + '\n')

    auto_close = False
    auto_close_path = "auto_close.txt"
    auto_close_path = get_full_path(auto_close_path)
    if os.path.exists(auto_close_path):
        auto_close = True
    logging.info("Finished")
    if not auto_close:
        input()

if __name__ == "__main__":
    main()