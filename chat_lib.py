CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
"login_msg": "LOGIN",
"logout_msg": "LOGOUT"
}

PROTOCOL_SERVER = {
"login_ok_msg": "LOGIN_OK",
"login_failed_msg": "ERROR"
}

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def split_data(data, amount_of_split):
    """
    this will separate the data by # into list
    :param data: string built like username#password
    :param amount_of_split: integer that point how much # has in data
    :return: list of values
    """
    return data.split('#') if amount_of_split == data.count('#') else None


def join_data(list_of_data):
    """
    this will connect the values in ths list with '#' to string
    :param list_of_data: list with values
    :return: string made from the list from ['a','b','c'] into 'a#b#c'
    """
    return "#".join(list_of_data)


def build_message(header, messege):
    """
    this will crate a messege to server
    :param header:string that will create to 16 length
    :param messege:the text that will transport to the user
    :return:16 letters|length of the messege|messege
    """
    return f"{header:16s}|{len(str(messege)):04d}|{messege}" if 0 <= len(header) <= 16 and 0 <= len(str(messege)) < 10000 else None


def parse_message(rec):
    """
    this will separete the messege by '|' and check if the messege match the number
    :param rec: 16 letters | 4 numbers | messege
    :return: list of the [header, messege]
    """
    mess = rec[rec.rfind("|") + 1:] if (int(rec[rec.find("|") + 1: rec.rfind("|")]) >= 0 and len(rec[rec.rfind("|") + 1:]) == (int(rec[rec.find("|") + 1: rec.rfind("|")])) if ''.join(rec[rec.find("|") + 1: rec.rfind("|")].split()).isnumeric() and rec.count("|") == 2 else None) else None
    head = "".join(rec[:rec.find("|")].split()) if len(rec[:rec.find("|")]) == 16 and mess is not None else None
    return head, mess
