import os
from collections import defaultdict

# ---------------- CONFIGURATION ----------------
PASS_PERCENT = 0.40
COLLEGE_CODE = "1AB"  # Based on your USN format
MAX_THEORY_MARKS = 130  # IA1+IA2+IA3(40+40+40) + Assignment(10) + External(40)
MAX_LAB_MARKS = 100     # Lab IA(50) + Continuous Eval(50)

# Based on your USN pattern: 1AB23CV001 - Year(23), Branch(CV), Number(001)
BRANCH_MAP = {
    "CV": "Civil Engineering",
    "CS": "Computer Science",
    "EC": "Electronics & Communication",
    "ME": "Mechanical Engineering",
    "AI": "Artificial Intelligence",
    "IS": "Information Science"
}

students = []

# ---------------- FILE READING ----------------
def read_students(filepath):
    """Read student data from the descriptive format file"""
    if not os.path.exists(filepath):
        print(f"ERROR: File '{filepath}' not found")
        return False
    
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        
        i = 0
        current_student = None
        subjects = []
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this is a new student section
            if line.startswith("Student") and line[7:].strip().isdigit():
                # If we have a previous student, add them to the list
                if current_student is not None:
                    current_student["subjects"] = subjects
                    students.append(current_student)
                
                # Start new student
                current_student = {}
                subjects = []
                i += 1
                continue
            
            # Parse student details
            if current_student is not None:
                # Parse Name
                if line.startswith("Name:"):
                    current_student["name"] = line[5:].strip()
                
                # Parse USN
                elif line.startswith("USN:"):
                    current_student["usn"] = line[4:].strip()
                
                # Parse Subject Name
                elif line.startswith("Subject Name:"):
                    subject_name = line[13:].strip()
                
                # Parse Subject Code
                elif line.startswith("Subject Code:"):
                    subject_code = line[13:].strip()
                
                # Parse IA1
                elif line.startswith("Sub(1IA):"):
                    try:
                        ia1 = int(line[9:].strip())
                    except:
                        ia1 = 0
                
                # Parse IA2
                elif line.startswith("Sub(2IA):"):
                    try:
                        ia2 = int(line[9:].strip())
                    except:
                        ia2 = 0
                
                # Parse IA3 - from your data format, it seems IA3 is not provided
                elif line.startswith("Sub(3IA):"):
                    try:
                        ia3 = int(line[9:].strip())
                    except:
                        ia3 = 0
                
                # Parse Assignment Marks
                elif line.startswith("Assignment Marks:"):
                    try:
                        assignment = int(line[17:].strip())
                    except:
                        assignment = 0
                
                # Parse External Marks
                elif line.startswith("Sub(Ext):"):
                    try:
                        external = int(line[9:].strip())
                    except:
                        external = 0
                
                # Parse Lab Subject Marks
                elif line.startswith("Lab Subject Marks:"):
                    try:
                        lab_total = int(line[18:].strip())
                    except:
                        lab_total = 0
                
                # Parse Lab IA Marks
                elif line.startswith("Lab IA Marks:"):
                    try:
                        lab_ia = int(line[13:].strip())
                    except:
                        lab_ia = 0
                
                # Parse Continuous Evaluation Marks
                elif line.startswith("Continuous Evaluation Marks:"):
                    try:
                        continuous_eval = int(line[27:].strip())
                    except:
                        continuous_eval = 0
                    
                    # At this point, we have all subject data, create subject entry
                    # Determine subject type based on available marks
                    subject_type = "IPCC" if (lab_ia > 0 or continuous_eval > 0) else "Normal"
                    
                    subject = {
                        "type": subject_type,
                        "name": subject_name,
                        "code": subject_code,
                        "ia": [ia1, ia2, 0],  # Assuming no IA3 in your data
                        "assignment": assignment,
                        "external": external,
                        "lab_ia": lab_ia,
                        "continuous_eval": continuous_eval
                    }
                    
                    subjects.append(subject)
                
                # Parse Fees per Year
                elif line.startswith("Fees per Year:"):
                    try:
                        fee_total = int(line[14:].strip())
                        current_student["fee_total"] = fee_total
                        # For your data, we don't have fee_paid, so we'll assume it's paid
                        current_student["fee_paid"] = fee_total  # Assuming full payment
                    except:
                        current_student["fee_total"] = 0
                        current_student["fee_paid"] = 0
                
                # Parse Mentor Name
                elif line.startswith("Mentor Name:"):
                    current_student["mentor"] = line[12:].strip()
            
            i += 1
        
        # Add the last student
        if current_student is not None:
            current_student["subjects"] = subjects
            students.append(current_student)
        
        print(f"Successfully loaded {len(students)} students")
        return True
        
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return False

# ---------------- LOGIC FUNCTIONS ----------------
def best_two_avg(ia_marks):
    """Find best 2 IA marks and return their average - requirement (b)"""
    if len(ia_marks) < 2:
        return 0, []
    
    # Filter out None values and ensure we have integers
    valid_marks = [m for m in ia_marks if m is not None]
    if len(valid_marks) < 2:
        return 0, valid_marks[:2]
    
    sorted_marks = sorted(valid_marks, reverse=True)
    best_two = sorted_marks[:2]
    average = sum(best_two) / 2.0
    return average, best_two

def calculate_theory_total(subject):
    """Calculate total theory marks"""
    avg_ia, best_two = best_two_avg(subject["ia"])
    total = avg_ia + subject["assignment"] + subject["external"]
    return total, avg_ia, best_two

def calculate_lab_total(subject):
    """Calculate total lab marks if applicable"""
    lab_ia = subject.get("lab_ia", 0)
    continuous_eval = subject.get("continuous_eval", 0)
    return lab_ia + continuous_eval

def check_subject_type(subject):
    """Determine subject type - requirement (c)"""
    lab_ia = subject.get("lab_ia", 0)
    continuous_eval = subject.get("continuous_eval", 0)
    
    if lab_ia > 0 and continuous_eval > 0:
        return "IPCC (Theory + Lab)"
    elif lab_ia > 0 or continuous_eval > 0:
        return "Normal Subject + Lab"
    else:
        return "Normal Subject"

def is_theory_passed(subject):
    """Check if theory part is passed (40% of 130 = 52)"""
    theory_total, _, _ = calculate_theory_total(subject)
    return theory_total >= (MAX_THEORY_MARKS * PASS_PERCENT)

def is_lab_passed(subject):
    """Check if lab part is passed (40% of 100 = 40)"""
    lab_ia = subject.get("lab_ia", 0)
    continuous_eval = subject.get("continuous_eval", 0)
    
    if lab_ia == 0 and continuous_eval == 0:
        return True  # No lab component
    
    lab_total = calculate_lab_total(subject)
    return lab_total >= (MAX_LAB_MARKS * PASS_PERCENT)

def is_eligible_for_exam(subject):
    """Check eligibility for main exam - requirements (d,e)"""
    sub_type = check_subject_type(subject)
    
    if "IPCC" in sub_type:
        # For IPCC subjects, both theory and lab must pass
        theory_pass = is_theory_passed(subject)
        lab_pass = is_lab_passed(subject)
        
        if not theory_pass and not lab_pass:
            return False, "Failed in both Theory and Lab"
        elif not theory_pass:
            return False, "Failed in Theory (minimum 40% required)"
        elif not lab_pass:
            return False, "Failed in Lab (minimum 40% required)"
        return True, "Eligible for main exam"
    
    elif "Lab" in sub_type:
        # For Normal Subject + Lab, both must pass
        theory_pass = is_theory_passed(subject)
        lab_pass = is_lab_passed(subject)
        
        if not theory_pass and not lab_pass:
            return False, "Failed in both Theory and Lab"
        elif not theory_pass:
            return False, "Failed in Theory (minimum 40% required)"
        elif not lab_pass:
            return False, "Failed in Lab (minimum 40% required)"
        return True, "Eligible for main exam"
    
    else:
        # For normal subjects, only theory needs to pass
        if not is_theory_passed(subject):
            return False, "Failed in Theory (minimum 40% required)"
        return True, "Eligible for main exam"

def calculate_grade(total_marks, max_marks=100):
    """Calculate grade based on percentage - requirement (k)"""
    percentage = (total_marks / max_marks) * 100
    
    if percentage >= 70:
        return "Distinction", percentage
    elif percentage >= 60:
        return "First Class", percentage
    elif percentage >= 50:
        return "Second Class", percentage
    elif percentage >= 40:
        return "Pass", percentage
    else:
        return "Fail", percentage

def get_branch_from_usn(usn):
    """Extract branch from USN - requirement (m)"""
    if len(usn) >= 7:
        branch_code = usn[5:7]
        return BRANCH_MAP.get(branch_code, f"Branch Code: {branch_code}")
    return "Unknown Branch"

def is_college_student(usn):
    """Check if student belongs to our college - requirement (a)"""
    return usn.startswith(COLLEGE_CODE)

# ---------------- ANALYSIS FUNCTIONS ----------------
def analyze_students():
    """Perform comprehensive analysis of all students"""
    subject_stats = defaultdict(lambda: {
        "name": "",
        "pass_count": 0,
        "fail_count": 0,
        "students": [],
        "ia1_absent": 0,
        "ia2_absent": 0,
        "ia3_absent": 0,
        "assign_not_submitted": 0,
        "grades": {"Distinction": 0, "First Class": 0, "Second Class": 0, "Pass": 0, "Fail": 0}
    })
    
    fail_distribution = defaultdict(list)
    all_subjects_pass_fail = {"passed_all": 0, "failed_any": 0}
    
    for student in students:
        failed_subjects_count = 0
        
        for subject in student["subjects"]:
            code = subject["code"]
            name = subject["name"]
            stats = subject_stats[code]
            stats["name"] = name  # Store subject name
            
            # Track IA absences (assuming 0 means absent)
            for i, ia_mark in enumerate(subject["ia"]):
                if ia_mark == 0:
                    if i == 0:
                        stats["ia1_absent"] += 1
                    elif i == 1:
                        stats["ia2_absent"] += 1
                    elif i == 2:
                        stats["ia3_absent"] += 1
            
            # Track assignment submission
            if subject["assignment"] == 0:
                stats["assign_not_submitted"] += 1
            
            # Check eligibility
            eligible, reason = is_eligible_for_exam(subject)
            
            if eligible:
                stats["pass_count"] += 1
            else:
                stats["fail_count"] += 1
                failed_subjects_count += 1
            
            # Calculate grade for this subject
            theory_total, _, _ = calculate_theory_total(subject)
            grade, percentage = calculate_grade(theory_total, MAX_THEORY_MARKS)
            stats["grades"][grade] += 1
            
            # Store student performance for topper calculation
            stats["students"].append({
                "name": student["name"],
                "usn": student["usn"],
                "theory_total": theory_total,
                "lab_total": calculate_lab_total(subject),
                "grade": grade,
                "percentage": percentage,
                "eligible": eligible
            })
        
        # Track failure distribution
        fail_distribution[failed_subjects_count].append({
            "name": student["name"],
            "usn": student["usn"],
            "failed_count": failed_subjects_count
        })
        
        # Track overall pass/fail
        if failed_subjects_count == 0:
            all_subjects_pass_fail["passed_all"] += 1
        else:
            all_subjects_pass_fail["failed_any"] += 1
    
    return subject_stats, fail_distribution, all_subjects_pass_fail

# ---------------- DISPLAY FUNCTIONS ----------------
def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)

# ---------- REQUIREMENT (a): College Affiliation ----------
def check_college_affiliation():
    """a) Find whether a student belongs to our college or not."""
    print_header("a) COLLEGE AFFILIATION CHECK")
    
    print(f"College Code: {COLLEGE_CODE}")
    print(f"Checking {len(students)} students...")
    print("-" * 80)
    
    college_students = []
    non_college_students = []
    
    for student in students:
        if is_college_student(student["usn"]):
            college_students.append(student)
        else:
            non_college_students.append(student)
    
    print(f"\n✅ COLLEGE STUDENTS ({len(college_students)}):")
    print("-" * 40)
    for student in college_students:
        print(f"  {student['name']:25} | USN: {student['usn']:12}")
    
    print(f"\n❌ NON-COLLEGE STUDENTS ({len(non_college_students)}):")
    print("-" * 40)
    for student in non_college_students:
        print(f"  {student['name']:25} | USN: {student['usn']:12}")
    
    print(f"\n📊 SUMMARY: {len(college_students)} college students, {len(non_college_students)} non-college students")

# ---------- REQUIREMENT (b): Best 2 IA Marks ----------
def display_best_two_ia_marks():
    """b) Find the best of two IA marks and average of the same."""
    print_header("b) BEST 2 IA MARKS ANALYSIS")
    
    for student in students:
        print(f"\n🎓 {student['name']} ({student['usn']}):")
        for subject in student["subjects"]:
            avg_ia, best_two = best_two_avg(subject["ia"])
            print(f"  📚 {subject['name']}:")
            print(f"     All IA Marks: {subject['ia']}")
            print(f"     Best 2 Marks: {best_two}")
            print(f"     Average of Best 2: {avg_ia:.2f}")
            print(f"     Maximum Possible: 40")

# ---------- REQUIREMENT (c): Subject Type ----------
def display_subject_types():
    """c) Find subject is IPCC/Normal Subject/Normal Subject+Lab"""
    print_header("c) SUBJECT TYPE CLASSIFICATION")
    
    subject_type_count = {"IPCC (Theory + Lab)": 0, "Normal Subject + Lab": 0, "Normal Subject": 0}
    subject_details = {}
    
    for student in students:
        for subject in student["subjects"]:
            sub_type = check_subject_type(subject)
            subject_type_count[sub_type] += 1
            
            if subject["code"] not in subject_details:
                subject_details[subject["code"]] = {
                    "name": subject["name"],
                    "type": sub_type,
                    "students": []
                }
            subject_details[subject["code"]]["students"].append(student["name"])
    
    print("\n📊 SUBJECT TYPE DISTRIBUTION:")
    print("-" * 60)
    for sub_type, count in subject_type_count.items():
        print(f"  {sub_type}: {count}")
    
    print("\n📋 DETAILED SUBJECT INFORMATION:")
    print("-" * 60)
    for code, details in subject_details.items():
        print(f"\n{details['name']} ({code}):")
        print(f"  Type: {details['type']}")
        print(f"  Number of students: {len(details['students'])}")

# ---------- REQUIREMENTS (d,e): Eligibility Check ----------
def check_exam_eligibility():
    """d,e) Check eligibility for main exam based on subject type"""
    print_header("d,e) EXAM ELIGIBILITY CHECK")
    
    print("Minimum Passing Criteria:")
    print(f"  Theory: {MAX_THEORY_MARKS * PASS_PERCENT:.0f}/{MAX_THEORY_MARKS} (40%)")
    print(f"  Lab: {MAX_LAB_MARKS * PASS_PERCENT:.0f}/{MAX_LAB_MARKS} (40%)")
    print("-" * 80)
    
    eligible_count = 0
    not_eligible_count = 0
    
    for student in students:
        print(f"\n🎓 {student['name']} ({student['usn']}):")
        all_eligible = True
        
        for subject in student["subjects"]:
            sub_type = check_subject_type(subject)
            eligible, reason = is_eligible_for_exam(subject)
            theory_total, _, _ = calculate_theory_total(subject)
            lab_total = calculate_lab_total(subject)
            
            print(f"\n  📚 {subject['name']} ({subject['code']}) - {sub_type}:")
            print(f"     Theory Marks: {theory_total}/{MAX_THEORY_MARKS} ({theory_total/MAX_THEORY_MARKS*100:.1f}%)")
            
            if lab_total > 0:
                print(f"     Lab Marks: {lab_total}/{MAX_LAB_MARKS} ({lab_total/MAX_LAB_MARKS*100:.1f}%)")
            
            if eligible:
                print(f"     ✅ ELIGIBLE for main exam")
            else:
                print(f"     ❌ NOT ELIGIBLE for main exam")
                print(f"     Reason: {reason}")
                all_eligible = False
        
        if all_eligible:
            eligible_count += 1
            print(f"\n  ✅ OVERALL: ELIGIBLE FOR ALL EXAMS")
        else:
            not_eligible_count += 1
            print(f"\n  ❌ OVERALL: NOT ELIGIBLE FOR SOME EXAMS")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Eligible for all exams: {eligible_count} students")
    print(f"  Not eligible for some exams: {not_eligible_count} students")

# ---------- REQUIREMENT (f): Pass/Fail per Subject ----------
def display_pass_fail_per_subject(subject_stats):
    """f) Find number of students passed and failed in each subject."""
    print_header("f) PASS/FAIL COUNT PER SUBJECT")
    
    print("Subject-wise Pass/Fail Statistics:")
    print("-" * 80)
    print(f"{'Subject Code':15} {'Subject Name':30} {'Passed':10} {'Failed':10} {'Total':10}")
    print("-" * 80)
    
    for code, stats in subject_stats.items():
        passed = stats["pass_count"]
        failed = stats["fail_count"]
        total = passed + failed
        pass_percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"{code:15} {stats['name'][:30]:30} {passed:10} {failed:10} {total:10}")
        print(f"{'':15} {'Pass Rate:':30} {pass_percentage:10.1f}%")

# ---------- REQUIREMENT (g): Top 3 Toppers per Subject ----------
def display_top_toppers_per_subject(subject_stats):
    """g) Find top 3 toppers in each subject."""
    print_header("g) TOP 3 TOPPERS IN EACH SUBJECT")
    
    for code, stats in subject_stats.items():
        print(f"\n🏆 {stats['name']} ({code}):")
        
        if stats["students"]:
            sorted_students = sorted(stats["students"], key=lambda x: x["theory_total"], reverse=True)
            print(f"{'Rank':5} {'Name':25} {'USN':15} {'Marks':10} {'Grade':15}")
            print("-" * 70)
            
            for i, stud in enumerate(sorted_students[:3], 1):
                print(f"{i:5} {stud['name']:25} {stud['usn']:15} {stud['theory_total']:7}/130 {stud['grade']:15}")
        else:
            print("  No student data available")

# ---------- REQUIREMENT (h): Top 3 Class Toppers ----------
def display_top_class_toppers():
    """h) Find top 3 toppers of a class."""
    print_header("h) TOP 3 CLASS TOPPERS")
    
    class_performance = []
    for student in students:
        total_marks = 0
        subjects_count = len(student["subjects"])
        
        for subject in student["subjects"]:
            theory_total, _, _ = calculate_theory_total(subject)
            total_marks += theory_total
        
        if subjects_count > 0:
            average_percentage = (total_marks / (subjects_count * MAX_THEORY_MARKS)) * 100
            grade, _ = calculate_grade(average_percentage, 100)
            class_performance.append({
                "name": student["name"],
                "usn": student["usn"],
                "total_marks": total_marks,
                "subjects": subjects_count,
                "average": average_percentage,
                "grade": grade
            })
    
    # Sort by average percentage
    sorted_students = sorted(class_performance, key=lambda x: x["average"], reverse=True)
    
    print("🏆 TOP 3 CLASS TOPPERS:")
    print("-" * 80)
    print(f"{'Rank':5} {'Name':25} {'USN':15} {'Average %':12} {'Grade':15}")
    print("-" * 80)
    
    for i, student in enumerate(sorted_students[:3], 1):
        print(f"{i:5} {student['name']:25} {student['usn']:15} {student['average']:11.2f}% {student['grade']:15}")
        print(f"{'':5} Total Marks: {student['total_marks']}/{student['subjects']*MAX_THEORY_MARKS} across {student['subjects']} subjects")

# ---------- REQUIREMENT (i): Failure Distribution ----------
def display_failure_distribution(fail_distribution):
    """i) Find students failed in specific number of subjects."""
    print_header("i) FAILURE DISTRIBUTION BY SUBJECT COUNT")
    
    print("Number of students failed in specific number of subjects:")
    print("-" * 80)
    
    total_failures = 0
    for fail_count in sorted(fail_distribution.keys()):
        students_list = fail_distribution[fail_count]
        count = len(students_list)
        total_failures += count * fail_count
        
        if fail_count == 0:
            print(f"\n✅ {fail_count} subjects failed: {count} student(s) - ALL PASSED!")
        else:
            print(f"\n❌ {fail_count} subject(s) failed: {count} student(s)")
        
        for student in students_list:
            status = "✅ PASSED ALL" if fail_count == 0 else f"❌ Failed in {fail_count} subject(s)"
            print(f"  • {student['name']} ({student['usn']}) - {status}")

# ---------- REQUIREMENT (j): Overall Pass/Fail ----------
def display_overall_pass_fail(all_subjects_pass_fail):
    """j) Find number of students passed and failed in each subject and all subjects."""
    print_header("j) OVERALL PASS/FAIL STATISTICS")
    
    total_students = len(students)
    passed_all = all_subjects_pass_fail["passed_all"]
    failed_any = all_subjects_pass_fail["failed_any"]
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Students: {total_students}")
    print(f"  Passed in ALL subjects: {passed_all} ({passed_all/total_students*100:.1f}%)")
    print(f"  Failed in ANY subject(s): {failed_any} ({failed_any/total_students*100:.1f}%)")
    
    if total_students > 0:
        print(f"\n🎯 SUCCESS RATE: {(passed_all/total_students*100):.1f}%")

# ---------- REQUIREMENT (k): Grade Distribution ----------
def display_grade_distribution(subject_stats):
    """k) Find distinctions, first class, second class and pass students."""
    print_header("k) GRADE DISTRIBUTION")
    
    # Calculate overall grades across all subjects
    overall_grades = {"Distinction": 0, "First Class": 0, "Second Class": 0, "Pass": 0, "Fail": 0}
    subject_grades = {}
    
    for code, stats in subject_stats.items():
        subject_grades[code] = stats["grades"].copy()
        for grade, count in stats["grades"].items():
            overall_grades[grade] += count
    
    print("\n📊 OVERALL GRADE DISTRIBUTION (All Subjects):")
    print("-" * 80)
    total_subjects = sum(overall_grades.values())
    
    for grade in ["Distinction", "First Class", "Second Class", "Pass", "Fail"]:
        count = overall_grades[grade]
        percentage = (count / total_subjects * 100) if total_subjects > 0 else 0
        print(f"  {grade:15}: {count:4} ({percentage:5.1f}%)")
    
    # Display students by grade
    print("\n👥 STUDENTS BY GRADE CATEGORY:")
    print("-" * 80)
    
    grade_categories = {}
    for student in students:
        grades = []
        for subject in student["subjects"]:
            theory_total, _, _ = calculate_theory_total(subject)
            grade, _ = calculate_grade(theory_total, MAX_THEORY_MARKS)
            grades.append(grade)
        
        # Get highest grade for the student
        grade_order = {"Distinction": 4, "First Class": 3, "Second Class": 2, "Pass": 1, "Fail": 0}
        highest_grade = max(grades, key=lambda g: grade_order.get(g, 0))
        
        if highest_grade not in grade_categories:
            grade_categories[highest_grade] = []
        grade_categories[highest_grade].append(student["name"])
    
    for grade in ["Distinction", "First Class", "Second Class", "Pass", "Fail"]:
        if grade in grade_categories:
            print(f"\n{grade}:")
            for name in grade_categories[grade]:
                print(f"  • {name}")

# ---------- REQUIREMENT (l): Fee Payment Status ----------
def check_fee_payment():
    """l) Check students paid college fees or not; if not show balance and mentor."""
    print_header("l) FEE PAYMENT STATUS")
    
    pending_fees = 0
    total_balance = 0
    
    print("Fee Payment Status of Students:")
    print("-" * 80)
    
    for student in students:
        balance = student["fee_total"] - student["fee_paid"]
        
        if balance > 0:
            pending_fees += 1
            total_balance += balance
            print(f"❌ {student['name']:25} | Balance: ₹{balance:9,} | Action: Meet {student['mentor']}")
        else:
            print(f"✅ {student['name']:25} | Fee Status: FULLY PAID")
    
    print(f"\n📊 FEE PAYMENT SUMMARY:")
    print(f"  Total Students: {len(students)}")
    print(f"  Students with pending fees: {pending_fees}")
    print(f"  Total pending amount: ₹{total_balance:,}")
    
    if pending_fees > 0:
        print(f"\n⚠️  {pending_fees} student(s) need to meet their mentors regarding fee payment!")

def display_check_fee_alert():
    """Send alert to mentor if fees are unpaid"""
    print_header("FEE PAYMENT ALERTS")

    alert_count = 0

    for student in students:
        if not student.get("fee_paid", True):
            alert_count += 1
            print(f"🚨 ALERT SENT")
            print(f"   Student : {student['name']}")
            print(f"   USN     : {student['usn']}")
            print(f"   Mentor  : {student['mentor']}")
            print(f"   Status  : Fees NOT PAID\n")

    if alert_count == 0:
        print("✅ All students have paid their fees.")

# ---------- REQUIREMENT (m): Display Student Branch ----------
def display_student_branches():
    """m) Display student branch."""
    print_header("m) STUDENT BRANCH INFORMATION")
    
    branch_distribution = {}
    
    for student in students:
        branch = get_branch_from_usn(student["usn"])
        if branch not in branch_distribution:
            branch_distribution[branch] = []
        branch_distribution[branch].append(student["name"])
    
    print("Branch-wise Student Distribution:")
    print("-" * 80)
    
    for branch, students_list in branch_distribution.items():
        print(f"\n{branch}:")
        print(f"  Number of students: {len(students_list)}")
        for name in students_list:
            print(f"  • {name}")

# ---------- REQUIREMENT (n): IA Absentees ----------
def display_ia_absentees(subject_stats):
    """n) Find students not appeared for each IA individually."""
    print_header("n) IA ATTENDANCE ANALYSIS")
    
    total_ia1_absent = 0
    total_ia2_absent = 0
    total_ia3_absent = 0
    
    print("IA Absentee Report:")
    print("-" * 80)
    
    for code, stats in subject_stats.items():
        total_ia1_absent += stats["ia1_absent"]
        total_ia2_absent += stats["ia2_absent"]
        total_ia3_absent += stats["ia3_absent"]
        
        print(f"\n{stats['name']} ({code}):")
        print(f"  IA1 Absent: {stats['ia1_absent']}")
        print(f"  IA2 Absent: {stats['ia2_absent']}")
        print(f"  IA3 Absent: {stats['ia3_absent']}")
    
    print(f"\n📊 TOTAL IA ABSENCES:")
    print(f"  IA1: {total_ia1_absent}")
    print(f"  IA2: {total_ia2_absent}")
    print(f"  IA3: {total_ia3_absent}")
    print(f"  Total: {total_ia1_absent + total_ia2_absent + total_ia3_absent}")

# ---------- REQUIREMENT (o): Assignment Submission ----------
def display_assignment_status(subject_stats):
    """o) Find students not submitted assignments."""
    print_header("o) ASSIGNMENT SUBMISSION STATUS")
    
    total_not_submitted = 0
    
    print("Assignment Submission Report:")
    print("-" * 80)
    
    for code, stats in subject_stats.items():
        total_not_submitted += stats["assign_not_submitted"]
        
        print(f"\n{stats['name']} ({code}):")
        print(f"  Assignments not submitted: {stats['assign_not_submitted']}")
        if stats["assign_not_submitted"] > 0:
            print(f"  Submission Rate: {(len(students) - stats['assign_not_submitted'])/len(students)*100:.1f}%")
    
    print(f"\n📊 OVERALL ASSIGNMENT SUBMISSION:")
    print(f"  Total assignments not submitted: {total_not_submitted}")
    print(f"  Overall submission rate: {(len(students)*len(subject_stats) - total_not_submitted)/(len(students)*len(subject_stats))*100:.1f}%")

# ---------- REQUIREMENT (p): Search by USN ----------
def search_student_by_usn():
    """p) Search student details based on USN."""
    print_header("p) SEARCH STUDENT BY USN")
    
    usn = input("Enter USN to search: ").strip().upper()
    
    found = False
    for student in students:
        if student["usn"] == usn:
            found = True
            print(f"\n" + "=" * 80)
            print("✅ STUDENT DETAILS FOUND")
            print("=" * 80)
            print(f"Name          : {student['name']}")
            print(f"USN           : {student['usn']}")
            print(f"Branch        : {get_branch_from_usn(student['usn'])}")
            print(f"Mentor        : {student['mentor']}")
            print(f"College       : {'YES' if is_college_student(student['usn']) else 'NO'}")
            
            # Fee status
            balance = student["fee_total"] - student["fee_paid"]
            if balance > 0:
                print(f"Fee Status    : PENDING (Balance: ₹{balance:,})")
                print(f"Action        : Meet mentor {student['mentor']}")
            else:
                print(f"Fee Status    : FULLY PAID")
            
            print(f"\nSUBJECT PERFORMANCE:")
            print("-" * 80)
            
            for i, subject in enumerate(student["subjects"], 1):
                sub_type = check_subject_type(subject)
                eligible_status, reason = is_eligible_for_exam(subject)
                
                theory_total, avg_ia, best_two = calculate_theory_total(subject)
                grade, percentage = calculate_grade(theory_total, MAX_THEORY_MARKS)
                lab_total = calculate_lab_total(subject)
                
                print(f"\n{i}. {subject['name']} ({subject['code']}) - {sub_type}")
                print(f"   Best 2 IA marks: {best_two} | Average: {avg_ia:.1f}")
                print(f"   Assignment: {subject['assignment']}/10 | External: {subject['external']}/40")
                print(f"   Theory Total: {theory_total}/130 ({percentage:.1f}%) - Grade: {grade}")
                
                if lab_total > 0:
                    print(f"   Lab IA: {subject.get('lab_ia', 0)}/50")
                    print(f"   Continuous Eval: {subject.get('continuous_eval', 0)}/50")
                    print(f"   Lab Total: {lab_total}/100 ({lab_total}%)")
                
                print(f"   Eligibility: {'✅ ELIGIBLE' if eligible_status else '❌ NOT ELIGIBLE'}")
                if not eligible_status:
                    print(f"   Reason: {reason}")
            
            print("\n" + "=" * 80)
            break
    
    if not found:
        print(f"\n❌ No student found with USN: {usn}")

# ---------------- MAIN MENU ----------------
def display_main_menu():
    """Display main menu in the sequence of requirements (a to p)"""
    print_header("STUDENT MANAGEMENT SYSTEM")
    print("\nMAIN MENU - Select an option (a-p):")
    print("=" * 80)
    print("a) Check college affiliation")
    print("b) Find best 2 IA marks and average")
    print("c) Classify subject types (IPCC/Normal/Normal+Lab)")
    print("d,e) Check exam eligibility")
    print("f) Pass/Fail count per subject")
    print("g) Top 3 toppers per subject")
    print("h) Top 3 class toppers")
    print("i) Failure distribution by subject count")
    print("j) Overall pass/fail statistics")
    print("k) Grade distribution (Distinction/First Class/Second Class/Pass)")
    print("l) Fee payment status")
    print("z) check_fee_alert")
    print("m) Display student branches")
    print("n) IA absentee analysis")
    print("o) Assignment submission status")
    print("p) Search student by USN")
    print("x) Display ALL reports")
    print("q) Exit")
    print("=" * 80)
    
    return input("\nEnter your choice (a-p, x, q): ").strip().lower()

# ---------------- MAIN PROGRAM ----------------
def main():
    """Main program function"""
    
    # File path - Update this with your actual file path
    file_path = r"path/to/your/data.txt"
    
    print("=" * 80)
    print("STUDENT MANAGEMENT SYSTEM - COMPLETE SOLUTION".center(80))
    print("=" * 80)
    
    # Read student data
    print("\n📂 Loading student data...")
    if not read_students(file_path):
        print("Failed to read student data. Exiting...")
        return
    
    if not students:
        print("No student data loaded. Exiting...")
        return
    
    print(f"✅ Successfully loaded {len(students)} students")
    
    # Perform analysis once
    print("\n📊 Analyzing student data...")
    subject_stats, fail_distribution, all_subjects_pass_fail = analyze_students()
    print("✅ Analysis complete!")
    
    # Interactive menu
    while True:
        choice = display_main_menu()
        
        if choice == "a":
            check_college_affiliation()
        elif choice == "b":
            display_best_two_ia_marks()
        elif choice == "c":
            display_subject_types()
        elif choice in ["d", "e"]:
            check_exam_eligibility()
        elif choice == "f":
            display_pass_fail_per_subject(subject_stats)
        elif choice == "g":
            display_top_toppers_per_subject(subject_stats)
        elif choice == "h":
            display_top_class_toppers()
        elif choice == "i":
            display_failure_distribution(fail_distribution)
        elif choice == "j":
            display_overall_pass_fail(all_subjects_pass_fail)
        elif choice == "k":
            display_grade_distribution(subject_stats)
        elif choice == "l":
            check_fee_payment()
        elif choice == "z":
            display_check_fee_alert()
        elif choice == "m":
            display_student_branches()
        elif choice == "n":
            display_ia_absentees(subject_stats)
        elif choice == "o":
            display_assignment_status(subject_stats)
        elif choice == "p":
            search_student_by_usn()
        elif choice == "x":
            # Display all reports in sequence
            print("\n📋 GENERATING COMPLETE REPORT...")
            check_college_affiliation()
            display_best_two_ia_marks()
            display_subject_types()
            check_exam_eligibility()
            display_pass_fail_per_subject(subject_stats)
            display_top_toppers_per_subject(subject_stats)
            display_top_class_toppers()
            display_failure_distribution(fail_distribution)
            display_overall_pass_fail(all_subjects_pass_fail)
            display_grade_distribution(subject_stats)
            display_check_fee_payment()
            display_student_branches()
            display_ia_absentees(subject_stats)
            display_assignment_status(subject_stats)
            print("\n✅ Complete report generated!")
        elif choice == "q":
            print("\n" + "=" * 80)
            print("Thank you for using Student Management System!".center(80))
            print("=" * 80)
            break
        else:
            print("❌ Invalid choice. Please enter a letter between a-p, x, or q.")
        
        input("\nPress Enter to continue...")

# ---------------- EXECUTION ----------------
if __name__ == "__main__":
    main()
