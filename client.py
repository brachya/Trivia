import socket
from typing import Optional
import chat_lib


class Client:
    def __init__(self, server_ip: str, server_port: int):
        self.SERVER_IP = server_ip
        self.SERVER_PORT = server_port
        self.connection = self.connect()

    def build_send_recv_parse(self, cmd: str, data: str) -> Optional[str]:
        self.build_and_send_message(cmd, data)
        _, value = self.recv_message_and_parse()
        return value

    def get_highscore(self) -> Optional[str]:
        return self.build_send_recv_parse("HIGHSCORE", "")

    def get_score(self):
        return self.build_send_recv_parse("MY_SCORE", "")

    def play_question(self):
        to_quest = self.build_send_recv_parse("GET_QUESTION", "")
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
                answer = self.build_send_recv_parse(
                    "SEND_ANSWER", chat_lib.join_data([question[0], user_answer])
                )
                if not answer:
                    print("CORRECT ANSWER!!!")
                else:
                    print("Wrong answer")
                    print(answer)

    def get_logged_users(self):
        return self.build_send_recv_parse("LOGGED", "")

    def build_and_send_message(self, code: str, data: str):
        """
        Builds a new message using chat_lib, wanted code and message.
        Prints debug info, then sends it to the given socket.
        :param code: code (str)
        :param data: data (str)
        :return: Nothing
        """
        to_send = chat_lib.build_message(code, data)
        if to_send is not None:
            self.connection.send(to_send.encode())

    def recv_message_and_parse(self):
        """
        Receives a new message from given socket,
        then parses the message using chat_lib.
        :return: cmd (str) and data (str) of the received message.
        If error occurred, will return None, None
        """
        full_msg = self.connection.recv(1024).decode()
        cmd, data = chat_lib.parse_message(full_msg)
        return cmd, data

    def connect(self) -> socket.socket:
        """create connection with the server"""
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((self.SERVER_IP, self.SERVER_PORT))
        return connection

    def error_and_exit(self, error_msg: str):
        print(error_msg)
        exit()

    def login(self):
        while True:
            username = input("Please enter username: \n")
            password = input("Please write password: \n")
            self.build_and_send_message(
                chat_lib.PROTOCOL_CLIENT["login_msg"],
                chat_lib.join_data([username, password]),
            )
            sev_ans = self.recv_message_and_parse()
            answer = chat_lib.build_message(
                chat_lib.PROTOCOL_SERVER["login_ok_msg"], ""
            )
            if answer is not None:
                if sev_ans == chat_lib.parse_message(answer):
                    print("Logged in!")
                    return
                else:
                    print(sev_ans[1])

    def logout(self):
        self.build_and_send_message(chat_lib.PROTOCOL_CLIENT["logout_msg"], "")
        self.connection.close()
        print("GoodBye!")

    def main(self):
        self.login()
        while True:
            choice = input(
                "q - Question\no - Logout\ns - Score\nu - Users\nh - Highscore\n"
            )
            self.play_question() if choice == "q" else choice
            print(self.get_score()) if choice == "s" else choice
            print(self.get_highscore()) if choice == "h" else choice
            print(self.get_logged_users()) if choice == "u" else choice
            if choice == "o":
                break
        self.logout()


if __name__ == "__main__":
    Client("127.0.0.1", 5678).main()
