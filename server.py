##############################################################################
# server.py
##############################################################################
import select
import socket
from typing import Any, Optional
import questions_uploader
import chat_lib
import random


class Server:
    # GLOBALS
    messages_to_send: list[tuple[socket.socket, Optional[str]]] = []
    questions: dict[int, dict[str, Any]] = {}
    logged_users: dict[socket.socket, str] = {}
    ERROR_MSG = "Error! "

    def __init__(self, ip: str, port: int) -> None:
        self.SERVER_PORT = port
        self.SERVER_IP = ip
        self.connection = self.setup_socket()
        self.users: dict[str, dict[str, Any]] = self.load_user_database()
        print("Welcome to Trivia Server!")
        print("Loading questions...")
        self.questions = questions_uploader.load_questions()
        print("questions loaded.")

    def build_and_send_message(self, conn: socket.socket, code: str, data: str) -> None:
        """
        Builds a new message using chat_lib, wanted code and message.
        Prints debug info, then sends it to the given socket.
        """
        print("[SERVER] ", code, data)  # Debug print
        self.messages_to_send.append((conn, chat_lib.build_message(code, data)))

    def recv_message_and_parse(
        self, conn: socket.socket
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Receives a new message from given socket,
        then parses the message using chat_lib.
        If error occurred, will return (None, None)
        """
        full_msg = conn.recv(1024).decode()
        cmd, data = chat_lib.parse_message(full_msg)
        print("[CLIENT] ", full_msg)  # Debug print
        return cmd, data

    # Data Loaders #

    def load_questions(self) -> dict[int, dict[str, Optional[str | list[str] | int]]]:
        """
        Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
        Returns: questions dictionary
        """
        questions_database: dict[int, dict[str, Optional[str | list[str] | int]]] = {
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

    def load_user_database(self) -> dict[str, dict[str, str | int | list[int]]]:
        """
        Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
        Returns: user dictionary
        """
        users_database: dict[str, dict[str, str | int | list[int]]] = {
            "test": {"password": "test", "score": 0, "questions_asked": []},
            "yossi": {"password": "123", "score": 50, "questions_asked": []},
            "master": {"password": "master", "score": 200, "questions_asked": []},
        }
        return users_database

    # SOCKET CREATOR

    def setup_socket(self) -> socket.socket:
        """
        Creates new listening socket and returns it
        Returns: the socket object
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        server_socket.listen()
        print("The server is running...")
        return server_socket

    def send_error(self, conn: socket.socket, error_msg: str) -> None:
        """
        Send error message with given message
        Receives: socket, message error string from called function
        """
        self.build_and_send_message(conn, "ERROR", error_msg)

    def handle_get_score_message(self, conn: socket.socket, username: str):
        self.build_and_send_message(conn, "SCORE", self.users[username]["score"])

    def handle_logout_message(self, conn: socket.socket) -> None:
        """
        Closes the given socket (in laster chapters, also remove user from logged_users dictionary)
        """
        self.logged_users.pop(conn)
        conn.close()
        print(f"client {conn} disconnected")

    def handle_logged_message(self, conn: socket.socket) -> None:
        """this will send to client the list of the logged users"""
        self.build_and_send_message(
            conn, "LOGGED_USERS", "\n".join(list(self.logged_users.values()))
        )

    def create_random_question(self) -> list[str]:
        """takes from questions random question and send to client"""
        randomly = random.choice(list(self.questions.keys()))
        return (
            [str(randomly)]
            + [self.questions[randomly]["question"]]
            + self.questions[randomly]["answers"]
        )

    def handle_question_message(self, conn: socket.socket):
        """send the question to client"""
        self.build_and_send_message(
            conn, "YOUR_QUESTION", chat_lib.join_data(self.create_random_question())
        )

    def handle_answer_message(
        self, conn: socket.socket, username: str, answer: str
    ) -> None:
        """get the answer from client and check if it is correct and send to client message"""
        answer_user = chat_lib.split_data(answer, 1)
        if answer_user is not None:
            question: Optional[str] = answer_user[0]
            ans: Optional[str] = answer_user[1]
            if self.questions[int(question)]["correct"] == int(ans):
                self.build_and_send_message(conn, "CORRECT_ANSWER", "")
                self.users[username]["score"] += 5
            else:
                self.build_and_send_message(
                    conn, "WRONG_ANSWER", self.questions[int(question)]["correct"]
                )

    def handle_highscore_message(self, conn: socket.socket) -> None:
        """this will send the highscore from high to low to the client"""
        high = sorted(self.users.items(), key=lambda x: x[1]["score"])
        highscore: list[str] = []
        for key in high:
            highscore.append(" ".join([key[0], str(key[1]["score"])]))
        highscore_int_str = "\n".join(highscore)
        self.build_and_send_message(conn, "HIGHSCORE", highscore_int_str)

    def handle_login_message(self, conn: socket.socket, data: str) -> None:
        """
        Gets socket and message data of login message. Checks  user and pass exists and match.
        If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
        Receives: socket, message code and data
        """
        user_password = chat_lib.split_data(data, 1)
        if user_password is not None:
            user = user_password[0]
            password = user_password[1]
            if user in self.users.keys():
                if password == self.users[user]["password"]:
                    self.logged_users[conn] = user
                    self.build_and_send_message(conn, "LOGIN_OK", "")
                else:
                    self.build_and_send_message(conn, "ERROR", "Password doesn't match")
            else:
                self.build_and_send_message(conn, "ERROR", "User doesn't found")

    def handle_client_message(self, conn: socket.socket, cmd: str, data: str) -> None:
        """Gets message code and data and calls the right function to handle command"""
        if conn not in self.logged_users.keys():
            self.handle_login_message(conn, data)
        else:
            if cmd == chat_lib.PROTOCOL_CLIENT["logout_msg"]:
                self.handle_logout_message(conn)
            elif cmd == "MY_SCORE":
                self.handle_get_score_message(conn, self.logged_users[conn])
            elif cmd == "LOGGED":
                self.handle_logged_message(conn)
            elif cmd == "HIGHSCORE":
                self.handle_highscore_message(conn)
            elif cmd == "GET_QUESTION":
                self.handle_question_message(conn)
            elif cmd == "SEND_ANSWER":
                self.handle_answer_message(conn, self.logged_users[conn], data)
            else:
                self.send_error(conn, "unexpected error!")

    def main(self) -> None:
        read_list: list[socket.socket] = []
        while True:
            ready_to_read, ready_to_write, _ = select.select(  # _ should be error_list
                [self.connection] + read_list, read_list, []
            )
            for client in ready_to_read:
                if client is self.connection:
                    client_socket, client_address = self.connection.accept()
                    read_list.append(client_socket)
                    print(f"{client_address} connected")
                else:
                    print(
                        f"New data from client {str(client).split(',')[len(str(client).split(',')) - 1].split(')')[0]}"
                    )
                    cmd_data = self.recv_message_and_parse(client)
                    cmd: Optional[str] = cmd_data[0]
                    data: Optional[str] = cmd_data[1]
                    if cmd is not None and data is not None:
                        self.handle_client_message(client, cmd, data)
                    if cmd == chat_lib.PROTOCOL_CLIENT["logout_msg"]:
                        read_list.remove(client)
                    elif not cmd and not data:
                        read_list.remove(client)
                for message in self.messages_to_send:
                    sock, packet = message
                    if packet is not None:
                        if client in ready_to_write:
                            sock.send(packet.encode())
                            self.messages_to_send.remove(message)


if __name__ == "__main__":
    Server("127.0.0.1", 5678).main()
