import random
from tkinter import Tk, Label, Entry, Button, StringVar, OptionMenu, Text, Scrollbar, END, Frame
from collections import deque
import time


class VirtualMemorySimulator:
    def __init__(self, num_frames):
        self.num_frames = num_frames
        self.frames = []
        self.page_faults = 0
        self.page_hits = 0

    def access_page(self, page):
        if page in self.frames:
            self.page_hits += 1
            return False  # No page fault
        else:
            self.page_faults += 1
            if len(self.frames) < self.num_frames:
                self.frames.append(page)
            else:
                self.replace_page(page)
            return True  # Page fault

    def replace_page(self, page):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def metrics(self):
        total_accesses = self.page_faults + self.page_hits
        return {
            "Page Faults": self.page_faults,
            "Page Hits": self.page_hits,
            "Page Fault Rate": self.page_faults / total_accesses if total_accesses else 0,
            "Hit Rate": self.page_hits / total_accesses if total_accesses else 0,
        }


class FIFO(VirtualMemorySimulator):
    def __init__(self, num_frames):
        super().__init__(num_frames)
        self.queue = deque()

    def replace_page(self, page):
        oldest = self.queue.popleft()
        self.frames.remove(oldest)
        self.frames.append(page)
        self.queue.append(page)


class LRU(VirtualMemorySimulator):
    def __init__(self, num_frames):
        super().__init__(num_frames)
        self.recent_usage = deque()

    def access_page(self, page):
        if page in self.frames:
            self.page_hits += 1
            self.recent_usage.remove(page)
            self.recent_usage.append(page)
            return False
        else:
            self.page_faults += 1
            if len(self.frames) < self.num_frames:
                self.frames.append(page)
            else:
                self.replace_page(page)
            self.recent_usage.append(page)
            return True

    def replace_page(self, page):
        lru_page = self.recent_usage.popleft()
        self.frames.remove(lru_page)
        self.frames.append(page)


class Optimal(VirtualMemorySimulator):
    def __init__(self, num_frames, future_references):
        super().__init__(num_frames)
        self.future_references = future_references

    def replace_page(self, page):
        farthest = 0
        victim = self.frames[0]
        for frame in self.frames:
            try:
                distance = self.future_references.index(frame)
            except ValueError:
                victim = frame
                break
            if distance > farthest:
                farthest = distance
                victim = frame
        self.frames.remove(victim)
        self.frames.append(page)


# GUI Implementation
class MemorySimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Memory Simulator")
        self.root.configure(bg="#ffffff")
        self.root.geometry("900x650")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main Frame
        self.main_frame = Frame(root, bg="#ffffff", padx=20, pady=20)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # GUI Elements
        self.frames_label = Label(
            self.main_frame, text="Number of Frames:", font=("Helvetica", 14,"bold"), bg="#ffffff", fg="#000000"
        )
        self.frames_label.grid(row=0, column=0, sticky="w", pady=10)

        self.frames_input = Entry(self.main_frame, font=("Helvetica", 14), bg="#f0f0f0", fg="#000000", insertbackground="black")
        self.frames_input.grid(row=0, column=1, sticky="ew", pady=10)

        self.sequence_label = Label(
            self.main_frame, text="Page Sequence (comma-separated):", font=("Helvetica", 14,"bold"), bg="#ffffff", fg="#000000"
        )
        self.sequence_label.grid(row=1, column=0, sticky="w", pady=10)

        self.sequence_input = Entry(self.main_frame, font=("Helvetica", 14), bg="#f0f0f0", fg="#000000", insertbackground="black")
        self.sequence_input.grid(row=1, column=1, sticky="ew", pady=10)

        self.algorithm_label = Label(
            self.main_frame, text="Page Replacement Algorithm:", font=("Helvetica", 14,"bold"), bg="#ffffff", fg="#000000"
        )
        self.algorithm_label.grid(row=2, column=0, sticky="w", pady=10)

        self.algorithm_var = StringVar(self.root)
        self.algorithm_var.set("FIFO")  # Default algorithm
        self.algorithm_menu = OptionMenu(self.main_frame, self.algorithm_var, "FIFO", "LRU", "Optimal")
        self.algorithm_menu.config(font=("Helvetica", 14,"bold"), bg="#e7e7e7", fg="#000000")
        self.algorithm_menu.grid(row=2, column=1, sticky="ew", pady=10)
        self.run_button = Button(
        self.main_frame,

        text="Run Simulation",
        font=("Helvetica", 14, "bold"),
        bg="black",  # A darker blue for better visibility
        fg="black",    # White text for high contrast
        activebackground="#A9A9A9",  # Slightly darker blue when pressed
        activeforeground="grey",    # White text remains on hover or press
        command=self.run_simulation,
        )
        self.run_button.grid(row=3, column=0, columnspan=2, pady=4)


        # Scrollable Text Area
        self.text_frame = Frame(self.main_frame)
        self.text_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")

        self.result_text = Text(
            self.text_frame, font=("Courier", 14), bg="#e8f5e9", wrap="word", fg="#000000", insertbackground="black"
        )
        self.result_text.pack(side="left", fill="both", expand=True)

        self.scrollbar = Scrollbar(self.text_frame, command=self.result_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.result_text.configure(yscrollcommand=self.scrollbar.set)

    def dynamic_update(self, text):
        self.result_text.insert(END, text + "\n")
        self.result_text.see(END)
        self.result_text.update_idletasks()
        time.sleep(0.5)

    def run_simulation(self):
        # Clear the results display
        self.result_text.delete(1.0, END)

        # Get user inputs
        try:
            num_frames = int(self.frames_input.get())
            page_sequence = list(map(int, self.sequence_input.get().split(',')))
            algorithm = self.algorithm_var.get()

            # Choose algorithm
            if algorithm == "FIFO":
                simulator = FIFO(num_frames)
            elif algorithm == "LRU":
                simulator = LRU(num_frames)
            elif algorithm == "Optimal":
                simulator = Optimal(num_frames, page_sequence)
            else:
                self.dynamic_update("Invalid algorithm selected.")
                return

            # Run simulation dynamically
            self.dynamic_update("Starting Simulation...\n")
            for page in page_sequence:
                fault = simulator.access_page(page)
                self.dynamic_update(
                    f"Accessed Page: {page}, {'Fault' if fault else 'Hit'}, Frames: {simulator.frames}"
                )

            # Display metrics
            metrics = simulator.metrics()
            self.dynamic_update("\nSimulation Results:")
            for key, value in metrics.items():
                self.dynamic_update(f"{key}: {value:.2f}")

        except ValueError:
            self.dynamic_update("Error: Please provide valid inputs.")


if __name__ == "__main__":
    root = Tk()
    app = MemorySimulatorGUI(root)
    root.mainloop()
