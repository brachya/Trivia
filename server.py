##############################################################################
# server.py
##############################################################################
import select
import socket

import questions_uploader
import chat_lib
import random

# GLOBALS
messages_to_send = []
users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"
# SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS


def build_and_send_message(conn, code, data):
    """
    Builds a new message using chat_lib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    :param conn: conn (socket object)
    :param code: code (str)
    :param data: data (str)
    :return: Nothing
    """
    global messages_to_send
    print("[SERVER] ", code, data)  # Debug print
    messages_to_send.append((conn, chat_lib.build_message(code, data)))


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chat_lib.
    :param conn: conn (socket object)
    :return: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(1024).decode()
    cmd, data = chat_lib.parse_message(full_msg)
    print("[CLIENT] ", full_msg)  # Debug print
    return cmd, data


# Data Loaders #


def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions_database = {
        2313: {
            "question": "How much is 2+2",
            "answers": ["3", "4", "2", "1"],
            "correct": 2,
        },
        4122: {
            "question": "What is the capital of France?",
            "answers": ["Lion", "Marseille", "Paris", "Montpellier"],
            "correct": 3,
        },
    }
    return questions_database


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users_database = {
        "test": {"password": "test", "score": 0, "questions_asked": []},
        "yossi": {"password": "123", "score": 50, "questions_asked": []},
        "master": {"password": "master", "score": 200, "questions_asked": []},
    }
    return users_database


# SOCKET CREATOR


def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    print("The server is running...")
    return server_socket


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, "ERROR", error_msg)


def handle_getscore_message(conn, username):
    global users
    build_and_send_message(conn, "SCORE", users[username]["score"])


def handle_logout_message(conn):
    """
    Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: None
    """
    global logged_users
    logged_users.pop(conn)
    conn.close()
    print(f"client {conn} disconnected")

    # Implement code ...


def handle_logged_message(conn):
    """
    this will send to client the list of the logged users
    :param conn: socket
    :return:None
    """
    global logged_users
    build_and_send_message(conn, "LOGGED_USERS", list(logged_users.values()))


def create_random_question():
    """

    :return:
    """
    global questions
    randomaly = random.choice(list(questions.keys()))
    return (
        [str(randomaly)]
        + [questions[randomaly]["question"]]
        + questions[randomaly]["answers"]
    )


def handle_question_message(conn):
    """

    :param conn:
    :return:
    """
    build_and_send_message(
        conn, "YOUR_QUESTION", chat_lib.join_data(create_random_question())
    )


def handle_answer_message(conn, username, answer):
    """

    :param conn:
    :param username:
    :param answer:
    :return:
    """
    global users
    global questions
    answer_user = chat_lib.split_data(answer, 1)
    question, ans = answer_user[0], answer_user[1]
    if questions[int(question)]["correct"] == int(ans):
        build_and_send_message(conn, "CORRECT_ANSWER", "")
        users[username]["score"] += 5
    else:
        build_and_send_message(
            conn, "WRONG_ANSWER", questions[int(question)]["correct"]
        )


def handle_highscore_message(conn):
    """
    this will send the highscore from high to low to the client
    :param conn: socket
    :return:None
    """
    global users
    high = sorted(users.items(), key=lambda x: x[1]["score"])
    highscores = []
    for key in high:
        highscores.append(" ".join([key[0], str(key[1]["score"])]))
    highscores = "\n".join(highscores)
    build_and_send_message(conn, "HIGHSCORE", highscores)


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later
    user, password = chat_lib.split_data(data, 1)
    if user in users.keys():
        if password == users[user]["password"]:
            logged_users[conn] = user
            build_and_send_message(conn, "LOGIN_OK", "")
        else:
            build_and_send_message(conn, "ERROR", "Password doesn't match")
    else:
        build_and_send_message(conn, "ERROR", "User doesn't found")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users  # To be used later
    if conn not in logged_users.keys():
        handle_login_message(conn, data)
    else:
        if cmd == chat_lib.PROTOCOL_CLIENT["logout_msg"]:
            handle_logout_message(conn)
        elif cmd == "MY_SCORE":
            handle_getscore_message(conn, logged_users[conn])
        elif cmd == "LOGGED":
            handle_logged_message(conn)
        elif cmd == "HIGHSCORE":
            handle_highscore_message(conn)
        elif cmd == "GET_QUESTION":
            handle_question_message(conn)
        elif cmd == "SEND_ANSWER":
            handle_answer_message(conn, logged_users[conn], data)
        else:
            send_error(conn, "unexpected error!")

    # Implement code ...


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions
    global messages_to_send
    print("Welcome to Trivia Server!")
    connection = setup_socket()
    users = load_user_database()
    print("Loading qustions...")
    questions = questions_uploader.load_questions()
    print("questions loaded.")
    read_list = []
    while True:
        ready_to_read, ready_to_write, error_list = select.select(
            [connection] + read_list, read_list, []
        )
        for client in ready_to_read:
            if client is connection:
                client_socket, client_address = connection.accept()
                read_list.append(client_socket)
                print(f"{client_address} connected")
            else:
                print(
                    f"New data from client {str(client).split(',')[len(str(client).split(',')) - 1].split(')')[0]}"
                )
                cmd, data = recv_message_and_parse(client)
                handle_client_message(client, cmd, data)
                if cmd == chat_lib.PROTOCOL_CLIENT["logout_msg"]:
                    read_list.remove(client)
                elif not cmd and not data:
                    read_list.remove(client)
            for message in messages_to_send:
                sock, packet = message
                if client in ready_to_write:
                    sock.send(packet.encode())
                    messages_to_send.remove(message)

    # Implement code ...


if __name__ == "__main__":
    main()
