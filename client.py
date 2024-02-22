import socket
import chat_lib

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
# SERVER_PORT = 5555
SERVER_PORT = 5678


# HELPER SOCKET METHODS


def build_send_recv_parse(conn: socket.socket, cmd: str, data: str):
    build_and_send_message(conn, cmd, data)
    _, value = recv_message_and_parse(conn)
    return value


def get_highscore(conn: socket.socket):
    return build_send_recv_parse(conn, "HIGHSCORE", "")


def get_score(conn: socket.socket):
    return build_send_recv_parse(conn, "MY_SCORE", "")


def play_question(conn: socket.socket):
    to_quest = build_send_recv_parse(conn, "GET_QUESTION", "")
    if to_quest is not None:
        question = chat_lib.split_data(to_quest, 5)
        if not question:
            print("GameOver!")
        else:
            print(
                f"{question[1]}?\n\t\t1.{question[2]}\n\t\t2.{question[3]}\n\t\t3.{question[4]}\n\t\t4.{question[5]}"
            )
            while True:
                user_answer = input("What is the answer?\n")
                if user_answer in ["1", "2", "3", "4"]:
                    break
                else:
                    print("Wrong input!")
            answer = build_send_recv_parse(
                conn, "SEND_ANSWER", chat_lib.join_data([question[0], user_answer])
            )
            if not answer:
                print("CORRECT ANSWER!!!")
            else:
                print("Wrong answer")
                print(answer)


def get_logged_users(conn: socket.socket):
    return build_send_recv_parse(conn, "LOGGED", "")


def build_and_send_message(conn: socket.socket, code: str, data: str):
    """
    Builds a new message using chat_lib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    :param conn: conn (socket object)
    :param code: code (str)
    :param data: data (str)
    :return: Nothing
    """
    to_send = chat_lib.build_message(code, data)
    if to_send is not None:
        conn.send(to_send.encode())


def recv_message_and_parse(conn: socket.socket):
    """
    Receives a new message from given socket,
    then parses the message using chat_lib.
    :param conn: conn (socket object)
    :return: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    full_msg = conn.recv(1024).decode()
    cmd, data = chat_lib.parse_message(full_msg)
    return cmd, data


def connect():
    """ """
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((SERVER_IP, SERVER_PORT))
    return connection


def error_and_exit(error_msg: str):
    print(error_msg)
    exit()


def login(conn: socket.socket):
    while True:
        username = input("Please enter username: \n")
        password = input("Please write password: \n")
        build_and_send_message(
            conn,
            chat_lib.PROTOCOL_CLIENT["login_msg"],
            chat_lib.join_data([username, password]),
        )
        sev_ans = recv_message_and_parse(conn)
        answer = chat_lib.build_message(chat_lib.PROTOCOL_SERVER["login_ok_msg"], "")
        if answer is not None:
            if sev_ans == chat_lib.parse_message(answer):
                print("Logged in!")
                return
            else:
                print(sev_ans[1])


def logout(conn: socket.socket):
    build_and_send_message(conn, chat_lib.PROTOCOL_CLIENT["logout_msg"], "")
    conn.close()
    print("GoodBye!")


def main():
    connection = connect()
    login(connection)
    while True:
        choice = input("q - Question o - Logout s - Score u - Users h - Highscore\n")
        play_question(connection) if choice == "q" else choice
        print(get_score(connection)) if choice == "s" else choice
        print(get_highscore(connection)) if choice == "h" else choice
        print(get_logged_users(connection)) if choice == "u" else choice
        if choice == "o":
            break
    logout(connection)


if __name__ == "__main__":
    main()
