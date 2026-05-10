from tkinter import Tk, Label, Entry, Button
from services import InternalDatabaseService
import requests


class GPA_Calculator_App:
    def __init__(self):
        self.db_service = InternalDatabaseService(port=2039)
        self.db_service.start()

        self.last_row = -1

        self.master = Tk()
        self.master.title("GPA Calculator")
        
        self.master.geometry("500x500")

        self.label = Label(self.master, text="Enter your grade:")
        self.label.pack()

        self.entry = Entry(self.master)
        self.entry.pack()

        self.label2 = Label(self.master, text="Enter the workaload:")
        self.label2.pack()

        self.entry2 = Entry(self.master)
        self.entry2.pack()

        self.store_grade_btn = Button(self.master, text="Store Grade", command=self.add_grade)
        self.store_grade_btn.pack()

        self.calculate_button = Button(self.master, text="Calculate GPA", command=self.calculate_gpa)
        self.calculate_button.pack()

        self.result_label = Label(self.master, text="")
        self.result_label.pack()

    def add_grade(self):
        grade = self.entry.get()
        workload = self.entry2.get()
        # Here you can add code to store the grade and workload in a database or a file
        requests.post(f"http://localhost:2039/operation?action=post_cell&column=grades&row={self.last_row + 1}&value={grade}")
        requests.post(f"http://localhost:2039/operation?action=post_cell&column=workload&row={self.last_row + 1}&value={workload}")
        self.last_row += 1

    def calculate_gpa(self):
        numerator_sum = 0
        denominator_sum = 0
        for i in range(self.last_row + 1):
            # Retrieve the grade and workload for each row
            grade_response = requests.get(f"http://localhost:2039/operation?action=get_cell&column=grades&row={i}")
            workload_response = requests.get(f"http://localhost:2039/operation?action=get_cell&column=workload&row={i}")

            grade = float(grade_response.text)
            workload = float(workload_response.text)

            numerator_sum += grade * workload
            denominator_sum += workload

        if denominator_sum == 0:
            self.result_label.config(text="No valid grades to calculate GPA.")
        else:
            gpa = (numerator_sum / denominator_sum)*4/10
            self.result_label.config(text=f"Your GPA is: {gpa:.2f}")


if __name__ == "__main__":
    app = GPA_Calculator_App()
    app.master.mainloop()