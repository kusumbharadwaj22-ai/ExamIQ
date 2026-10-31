// ExamIQ - C++ analytics backend
// Called from Python (Flask) using subprocess.
// Usage: analytics analyze STUDENT_ID m1 m2 m3 m4 m5
//
// Computing aptitude concepts demonstrated in this file:
//   1. Arrays              -> marks[5] and digitCount[10]
//   2. Pointers            -> totalUsingPointer(), averageUsingPointer()
//   3. Variadic functions  -> sumOf(), minOf(), maxOf() using <cstdarg>
//   4. Classes and objects -> class Student
//   5. Loops & conditions  -> grade, result, digit counting
//   6. Number operations   -> digit-frequency of the student ID

#include <iostream>
#include <string>
#include <cstdarg>
#include <cstdlib>
using namespace std;

const int SUBJECTS = 5;

// ---------- 3. VARIADIC FUNCTIONS ----------
// The first argument tells the function how many numbers follow.
int sumOf(int count, ...) {
    va_list args;
    va_start(args, count);
    int total = 0;
    for (int i = 0; i < count; i++) total += va_arg(args, int);
    va_end(args);
    return total;
}

int minOf(int count, ...) {
    va_list args;
    va_start(args, count);
    int smallest = va_arg(args, int);
    for (int i = 1; i < count; i++) {
        int value = va_arg(args, int);
        if (value < smallest) smallest = value;
    }
    va_end(args);
    return smallest;
}

int maxOf(int count, ...) {
    va_list args;
    va_start(args, count);
    int largest = va_arg(args, int);
    for (int i = 1; i < count; i++) {
        int value = va_arg(args, int);
        if (value > largest) largest = value;
    }
    va_end(args);
    return largest;
}

// ---------- 2. POINTERS ----------
// 'arr' is a pointer to the first element; *(arr + i) is the i-th element.
int totalUsingPointer(const int* arr, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) total += *(arr + i);
    return total;
}

double averageUsingPointer(const int* arr, int n) {
    return (double)totalUsingPointer(arr, n) / n;
}

// ---------- 4. CLASS AND OBJECT ----------
class Student {
private:
    string id;
    int marks[SUBJECTS];          // 1. array of subject marks
public:
    Student(const string& studentId, const int values[]) {
        id = studentId;
        for (int i = 0; i < SUBJECTS; i++) marks[i] = values[i];
    }

    int total() const { return totalUsingPointer(marks, SUBJECTS); }
    double average() const { return averageUsingPointer(marks, SUBJECTS); }

    // Variadic functions are called with the five marks.
    int variadicTotal() const {
        return sumOf(5, marks[0], marks[1], marks[2], marks[3], marks[4]);
    }
    int minimum() const {
        return minOf(5, marks[0], marks[1], marks[2], marks[3], marks[4]);
    }
    int maximum() const {
        return maxOf(5, marks[0], marks[1], marks[2], marks[3], marks[4]);
    }

    // 5. Conditions: grade and result
    string grade() const {
        int t = total();
        if (t >= 400) return "A";
        else if (t >= 300) return "B";
        else if (t >= 200) return "C";
        return "Needs Support";
    }

    string result() const {
        for (int i = 0; i < SUBJECTS; i++)
            if (marks[i] < 33) return "FAIL";   // failing any subject = fail
        return "PASS";
    }

    // 6. Digit frequency of the student ID, stored in an array of 10 counters
    void digitFrequency(int digitCount[10]) const {
        for (int d = 0; d < 10; d++) digitCount[d] = 0;
        for (size_t i = 0; i < id.length(); i++)
            if (id[i] >= '0' && id[i] <= '9') digitCount[id[i] - '0']++;
    }
};

int main(int argc, char* argv[]) {
    if (argc != 3 + SUBJECTS || string(argv[1]) != "analyze") {
        cout << "{\"error\":\"Usage: analytics analyze STUDENT_ID m1 m2 m3 m4 m5\"}";
        return 1;
    }

    string studentId = argv[2];
    int marks[SUBJECTS];
    for (int i = 0; i < SUBJECTS; i++) marks[i] = atoi(argv[3 + i]);

    Student s(studentId, marks);          // creating an object

    int digitCount[10];
    s.digitFrequency(digitCount);

    // Print result as JSON so Python can read it
    cout << "{";
    cout << "\"total\":" << s.total() << ",";
    cout << "\"variadic_total\":" << s.variadicTotal() << ",";
    cout << "\"minimum\":" << s.minimum() << ",";
    cout << "\"maximum\":" << s.maximum() << ",";
    cout << "\"average\":" << s.average() << ",";
    cout << "\"grade\":\"" << s.grade() << "\",";
    cout << "\"result\":\"" << s.result() << "\",";
    cout << "\"digit_frequency\":{";
    bool first = true;
    for (int d = 0; d < 10; d++) {
        if (digitCount[d] > 0) {
            if (!first) cout << ",";
            cout << "\"" << d << "\":" << digitCount[d];
            first = false;
        }
    }
    cout << "}}";
    return 0;
}
