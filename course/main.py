import numpy as np
from threading import Thread

import channel_protocol

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"



class Screen:

    def __init__(self, w, h, x, y, r):
        self.width = w
        self.height = h
        self.radius = r
        self.centre = Point(x, y)
    pass

    def draw(self, ax):

        x_min = - self.width / 2
        x_max = + self.width / 2
        y_min = - self.height / 2
        y_max = + self.height / 2

        ax.plot([x_min, x_max, x_max, x_min, x_min], [y_max, y_max, y_min, y_min, y_max])

        sections = 630
        x = [self.centre.x + self.radius * np.cos(2 * np.pi * i / sections) for i in range(sections)]
        y = [self.centre.y + self.radius * np.sin(2 * np.pi * i / sections) for i in range(sections)]
        x.append(x[0])
        y.append(y[0])
        ax.plot(x, y)


class General:
    def __init__(self, index):
        self.connections = []
        self.conn_dirs = []
        self.conn_indexes = []
        self.is_corrupted = False
        self.index = index
        self.byzantine_result = None
        self.threshold = 0

    def add_connections(self, conn, conn_dir, index):
        self.connections.append(conn)
        self.conn_dirs.append(conn_dir)
        self.conn_indexes.append(index)

    def get_my_value_s1(self):
        return self.index

    @staticmethod
    def get_corrupted_value(n):
        return np.random.randint(n)

    @staticmethod
    def get_corrupted_tuples(n):
        return [np.random.randint(n) for i in range(n)]

    @staticmethod
    def get_corrupted_square_tuples(n):
        result = []
        for j in range(n):
            result.append([np.random.randint(n) for i in range(n)])
        return result

    def byzantine(self):
        # step 1
        # for all send my_value
        my_value = self.get_my_value_s1()
        n = len(self.connections) + 1

        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            if self.is_corrupted:
                my_value = self.get_corrupted_value(n)
            conn.send_message(my_value, conn_dir)

        # for all get values
        values = [None] * (len(self.connections) + 1)
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            new_value = None
            while new_value is None:
                new_value = conn.get_message(conn_dir)

            values[index] = new_value
        values[self.index] = my_value
        print(f"{self.index}: {values}\n", end="")
        # step 2
        # make tuple(..., value_i, ...)

        # step 3
        # for all send tuple
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            if self.is_corrupted:
                values = self.get_corrupted_tuples(len(values))

            conn.send_message(values, conn_dir)

        # for all get tuples
        values_arr = [None] * (len(self.connections) + 1)
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            new_values = None
            while new_values is None or not isinstance(new_values, list):
                new_values = conn.get_message(conn_dir)
                # print(f"{self.index}:{new_values}")

            values_arr[index] = new_values
        values_arr[self.index] = values

        print(f"{self.index}: {values_arr}\n", end="")

        # step 4
        # for all send square tuple
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            if self.is_corrupted:
                values_arr = self.get_corrupted_square_tuples(len(values_arr))

            conn.send_message(values_arr, conn_dir)

        # for all get square tuples
        values_arr_2 = [None] * (len(self.connections) + 1)
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            new_values = None
            while new_values is None or not isinstance(new_values[0], list):
                new_values = conn.get_message(conn_dir)
                # if not new_values is None:
                #     print(f"{self.index}:{new_values}:{isinstance(new_values[0], list)}")

            values_arr_2[index] = new_values
        values_arr_2[self.index] = values_arr

        print(f"{self.index}: {values_arr_2}\n", end="")

        # step 5
        # for square tuples compute true values

        # этап голосования
        result_values = np.empty(shape=(len(values_arr),len(values_arr)),dtype='object')
        for i in range(len(values_arr)):
            for j in range(len(values_arr)):
                other_values = []
                for k in range(len(values_arr)):
                    other_values.append(values_arr_2[k][i][j])

                unique_vals = set()
                for val in other_values:
                    unique_vals.add(val)

                tmp_res = {}
                for val in unique_vals:
                    count = other_values.count(val)
                    tmp_res[val] = count

                max_count = -1
                max_val = None
                for val in tmp_res:
                    if tmp_res[val] > max_count:
                        max_count = tmp_res[val]
                        max_val = val
                if max_count >= self.threshold:
                    result_values[i][j] = max_val

        values_arr = result_values
        print(f"{self.index}: {result_values}\n", end="")

        # step 6
        # for tuples compute true values

        # этап голосования
        result_values = [None] * len(values_arr)
        for i in range(len(values_arr)):
            other_values = []
            for j in range(len(values_arr)):
                other_values.append(values_arr[j][i])

            unique_vals = set()
            for val in other_values:
                unique_vals.add(val)

            tmp_res = {}
            for val in unique_vals:
                count = other_values.count(val)
                tmp_res[val] = count

            max_count = -1
            max_val = None
            for val in tmp_res:
                if tmp_res[val] > max_count:
                    max_count = tmp_res[val]
                    max_val = val
            if max_count >= self.threshold:
                result_values[i] = max_val

        # print(f"{self.index}:{result_values}\n", end="")
        self.byzantine_result = result_values

    def get_byzantine_result(self):
        return self.byzantine_result

    def stop_connections(self):
        for conn in self.connections:
            conn.stop()


def main():
    generals = []
    general_ths = []
    for i in range(7):
        generals.append(General(i))

    generals[5].is_corrupted = True
    generals[6].is_corrupted = True
    for i in range(len(generals)):
        generals[i].threshold = len(generals) - 2 - 1

    for i in range(len(generals)):
        for j in range(i+1, len(generals)):
            # print(f"{i}:{j}\n", end="")
            connection = channel_protocol.Connection()
            generals[i].add_connections(connection, 0, j)
            generals[j].add_connections(connection, 1, i)

    for camera in generals:
        general_ths.append(Thread(target=camera.byzantine))

    for cam_th in general_ths:
        cam_th.start()


    for cam_th in general_ths:
        cam_th.join()

    for i in range(len(generals)):
        generals[i].stop_connections()

    print("byzantine_result")
    for camera in generals:
        result_values = camera.get_byzantine_result()
        print(f"{camera.index}: {result_values}\n", end="")


if __name__ == "__main__":
    main()


3: [[[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [4, 0, 6, 3, 4, 3, 4], [1, 6, 1, 2, 0, 1, 4]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [3, 1, 2, 3, 5, 6, 4], [6, 0, 4, 5, 4, 4, 5]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [5, 2, 5, 1, 5, 4, 4], [5, 5, 0, 0, 4, 4, 4]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [5, 0, 0, 6, 5, 4, 6], [5, 2, 2, 3, 5, 4, 0]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [4, 1, 6, 4, 2, 6, 5], [3, 0, 6, 4, 0, 3, 0]],
    [[0, 2, 0, 2, 0, 5, 5], [5, 6, 2, 1, 5, 4, 1], [5, 0, 3, 0, 5, 1, 0], [1, 3, 4, 6, 2, 0, 4], [1, 1, 2, 0, 6, 6, 2], [6, 3, 2, 5, 3, 1, 6], [6, 2, 3, 0, 2, 5, 0]],
    [[3, 5, 3, 3, 4, 5, 6], [1, 2, 6, 6, 0, 4, 1], [1, 0, 6, 6, 3, 1, 1], [3, 1, 5, 2, 2, 1, 2], [5, 2, 3, 3, 0, 2, 2], [5, 6, 3, 3, 2, 2, 6], [1, 5, 0, 2, 6, 0, 0]]]
6: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None None None None], [None None None None None None None]]

4: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None 6 None None None None], [None 0 None None None 4 None]]

1: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None 5 None None], [None None None None None 4 None]]

0: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None None None None], [None None None None None 4 None]]


2: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None None None None],,[None None None None None 4 None]]
3: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None None None None], [None None None None None None 0]]
5: [[0 1 2 3 4 4 6], [0 1 2 3 4 4 4], [0 1 2 3 4 4 1], [0 1 2 3 4 4 1], [0 1 2 3 4 0 5], [None None None None None None None], [None None None None None None None]]


5: [[[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [4, 0, 6, 3, 4, 3, 4], [1, 6, 1, 2, 0, 1, 4]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [3, 1, 2, 3, 5, 6, 4], [6, 0, 4, 5, 4, 4, 5]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [5, 2, 5, 1, 5, 4, 4], [5, 5, 0, 0, 4, 4, 4]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [5, 0, 0, 6, 5, 4, 6], [5, 2, 2, 3, 5, 4, 0]],
    [[0, 1, 2, 3, 4, 4, 6], [0, 1, 2, 3, 4, 4, 4], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 4, 1], [0, 1, 2, 3, 4, 0, 5], [4, 1, 6, 4, 2, 6, 5], [3, 0, 6, 4, 0, 3, 0]],
    [[6, 3, 2, 1, 0, 3, 6], [6, 1, 5, 3, 1, 3, 6], [2, 4, 2, 2, 1, 4, 5], [6, 5, 0, 3, 5, 6, 5], [0, 6, 6, 1, 6, 5, 6], [3, 3, 1, 6, 6, 1, 2], [6, 2, 2, 4, 2, 6, 1]],
    [[1, 2, 6, 3, 2, 2, 5], [4, 3, 5, 6, 1, 1, 2], [1, 1, 1, 5, 5, 5, 4], [1, 1, 6, 2, 0, 2, 1], [1, 1, 5, 0, 4, 3, 4], [6, 4, 4, 1, 4, 3, 2], [3, 4, 2, 2, 1, 5, 5]]]