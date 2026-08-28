from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB = "lms.db"

@app.route("/healthz")
def healthz():
    return "OK", 200

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            course TEXT NOT NULL,
            mark INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, course_id, lesson_id)
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, course_id, lesson_id)
        );
    """)

    # Default users
    if not conn.execute(
        "SELECT 1 FROM users WHERE username = ?", ("admin",)
    ).fetchone():
        conn.execute(
            "INSERT INTO users(username, password, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )

    if not conn.execute(
        "SELECT 1 FROM users WHERE username = ?", ("student",)
    ).fetchone():
        conn.execute(
            "INSERT INTO users(username, password, role) VALUES (?, ?, ?)",
            ("student", generate_password_hash("student123"), "student")
        )

    # Default courses
    if not conn.execute("SELECT 1 FROM courses LIMIT 1").fetchone():
        conn.executemany(
            "INSERT INTO courses(name, description) VALUES (?, ?)",
            [
                (
                    "Cloud Computing",
                    "Introduction to cloud computing and cloud services."
                ),
                (
                    "Python Programming",
                    "Python programming fundamentals for beginners."
                ),
                (
                    "Database Systems",
                    "SQL, relational databases and database management."
                ),
                (
                    "AWS Cloud Essentials",
                    "Fundamentals of Amazon Web Services and cloud deployment."
                )
            ]
        )

    # Default learning materials
    if not conn.execute("SELECT 1 FROM materials LIMIT 1").fetchone():
        conn.executemany(
            "INSERT INTO materials(title, link) VALUES (?, ?)",
            [
                ("AWS Cloud Essentials", "#"),
                ("Python Notes", "#"),
                ("SQL Notes", "#")
            ]
        )

    conn.commit()
    conn.close()


# =========================================================
# COURSE-SPECIFIC CONTENT
#
# IMPORTANT:
# Content is selected by COURSE NAME, not only by lesson_id.
# Therefore /course/1 and /course/2 no longer use the same
# lesson/test data.
# =========================================================

COURSE_CONTENT = {

    "Cloud Computing": {
        "lessons": {
            1: {
                "title": "Lesson 1: Introduction",
                "content": """
                    <h3>Introduction to Cloud Computing</h3>

                    <p>
                        Cloud computing is the delivery of computing
                        services such as servers, storage, databases,
                        networking and software over the Internet.
                    </p>

                    <h4>Benefits</h4>
                    <ul>
                        <li>Scalability</li>
                        <li>Cost efficiency</li>
                        <li>Flexibility</li>
                        <li>High availability</li>
                    </ul>
                """
            },
            2: {
                "title": "Lesson 2: Fundamentals",
                "content": """
                    <h3>Cloud Computing Fundamentals</h3>

                    <p>
                        Cloud computing provides on-demand access to
                        computing resources through the Internet.
                    </p>

                    <h4>Three Main Service Models</h4>
                    <ul>
                        <li><strong>IaaS</strong> - Infrastructure as a Service</li>
                        <li><strong>PaaS</strong> - Platform as a Service</li>
                        <li><strong>SaaS</strong> - Software as a Service</li>
                    </ul>
                """
            },
            3: {
                "title": "Lesson 3: Practical Applications",
                "content": """
                    <h3>Practical Applications of Cloud Computing</h3>

                    <p>
                        Cloud computing is used for web hosting,
                        storage, databases, application development,
                        analytics, backup and collaboration.
                    </p>

                    <h4>Examples</h4>
                    <ul>
                        <li>Cloud storage</li>
                        <li>Web hosting</li>
                        <li>Database management</li>
                        <li>Data analytics</li>
                        <li>Backup and recovery</li>
                    </ul>
                """
            }
        },

        "tests": {
            1: [
                {
                    "question": "What is cloud computing?",
                    "options": [
                        "Delivery of computing services over the Internet",
                        "Only physical computer repair",
                        "A type of keyboard",
                        "A programming language"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is a benefit of cloud computing?",
                    "options": [
                        "Scalability",
                        "No Internet access",
                        "Only local storage",
                        "Limited resources"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is an example of a cloud service?",
                    "options": [
                        "Cloud storage",
                        "Paper notebook",
                        "USB keyboard",
                        "Desktop wallpaper"
                    ],
                    "answer": 0
                },
                {
                    "question": "Cloud resources can generally be accessed through:",
                    "options": [
                        "The Internet",
                        "Only a calculator",
                        "A printer cable",
                        "A keyboard"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is related to cloud computing?",
                    "options": [
                        "Servers",
                        "Paper files only",
                        "Mechanical pencils",
                        "Desk lamps"
                    ],
                    "answer": 0
                }
            ],
            2: [
                {
                    "question": "What does IaaS stand for?",
                    "options": [
                        "Infrastructure as a Service",
                        "Internet as a Software",
                        "Information as a System",
                        "Internal Application Service"
                    ],
                    "answer": 0
                },
                {
                    "question": "What does PaaS stand for?",
                    "options": [
                        "Platform as a Service",
                        "Program as a Server",
                        "Private Application System",
                        "Platform and Storage"
                    ],
                    "answer": 0
                },
                {
                    "question": "What does SaaS stand for?",
                    "options": [
                        "Software as a Service",
                        "Storage as a System",
                        "Server as a Software",
                        "Security as a Service"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which model provides an environment for application development?",
                    "options": ["PaaS", "SaaS", "IaaS", "LAN"],
                    "answer": 0
                },
                {
                    "question": "Which model provides virtual machines and infrastructure?",
                    "options": ["IaaS", "SaaS", "PaaS", "HTML"],
                    "answer": 0
                }
            ],
            3: [
                {
                    "question": "Which is a practical use of cloud computing?",
                    "options": [
                        "Web hosting",
                        "Paper filing",
                        "Manual typing only",
                        "Drawing with a pencil"
                    ],
                    "answer": 0
                },
                {
                    "question": "Cloud storage allows users to:",
                    "options": [
                        "Store and access files",
                        "Only print documents",
                        "Repair hardware",
                        "Replace a keyboard"
                    ],
                    "answer": 0
                },
                {
                    "question": "Cloud computing can be used for:",
                    "options": [
                        "Data analytics",
                        "Only handwriting",
                        "Physical books only",
                        "Manual calculations only"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is another application of cloud computing?",
                    "options": [
                        "Backup and recovery",
                        "Sharpening pencils",
                        "Cleaning monitors",
                        "Printing newspapers"
                    ],
                    "answer": 0
                },
                {
                    "question": "Cloud applications can help with:",
                    "options": [
                        "Online collaboration",
                        "Only offline work",
                        "Removing Internet access",
                        "Replacing all hardware"
                    ],
                    "answer": 0
                }
            ]
        }
    },

    "Python Programming": {
        "lessons": {
            1: {
                "title": "Lesson 1: Python Introduction",
                "content": """
                    <h3>Introduction to Python</h3>

                    <p>
                        Python is a high-level, interpreted programming
                        language known for its readable syntax.
                    </p>

                    <h4>Python Features</h4>
                    <ul>
                        <li>Easy-to-read syntax</li>
                        <li>Interpreted execution</li>
                        <li>Large standard library</li>
                        <li>Supports object-oriented programming</li>
                    </ul>
                """
            },
            2: {
                "title": "Lesson 2: Python Fundamentals",
                "content": """
                    <h3>Python Fundamentals</h3>

                    <p>
                        Python programs use variables, data types,
                        operators, conditions, loops and functions.
                    </p>

                    <h4>Common Data Types</h4>
                    <ul>
                        <li>Integer</li>
                        <li>Float</li>
                        <li>String</li>
                        <li>Boolean</li>
                        <li>List</li>
                    </ul>
                """
            },
           3: {
    "title": "Lesson 3: Practical Python",
    "content": """
        <h3>Practical Python</h3>

        <p>
            Python can be used to automate tasks, process data,
            build web applications and create scripts.
        </p>

        <h4>Practical Applications</h4>
        <ul>
            <li>Automation</li>
            <li>Data processing</li>
            <li>Web development</li>
            <li>File handling</li>
            <li>Application development</li>
        </ul>
    """
}
        },

        "tests": {
            1: [
                {
                    "question": "What type of language is Python?",
                    "options": [
                        "High-level programming language",
                        "Markup language",
                        "Database only",
                        "Operating system"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is a feature of Python?",
                    "options": [
                        "Readable syntax",
                        "Only machine code",
                        "No variables",
                        "No functions"
                    ],
                    "answer": 0
                },
                {
                    "question": "Python is commonly described as:",
                    "options": [
                        "Interpreted",
                        "Only compiled to hardware",
                        "A database",
                        "A web browser"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is commonly used with Python?",
                    "options": [
                        "Standard library",
                        "Only HTML",
                        "Only SQL",
                        "Only CSS"
                    ],
                    "answer": 0
                },
                {
                    "question": "Python supports:",
                    "options": [
                        "Object-oriented programming",
                        "Only spreadsheet editing",
                        "Only networking hardware",
                        "Only image viewing"
                    ],
                    "answer": 0
                }
            ],
            2: [
                {
                    "question": "Which is a Python data type?",
                    "options": ["Integer", "Monitor", "Keyboard", "Printer"],
                    "answer": 0
                },
                {
                    "question": "Which keyword is used to define a function?",
                    "options": ["def", "function", "func", "define"],
                    "answer": 0
                },
                {
                    "question": "Which data type stores text?",
                    "options": ["String", "Integer", "Boolean", "Float"],
                    "answer": 0
                },
                {
                    "question": "Which structure is used for repetition?",
                    "options": ["Loop", "Comment", "Import", "String"],
                    "answer": 0
                },
                {
                    "question": "Which value represents true/false?",
                    "options": ["Boolean", "String", "Float", "List"],
                    "answer": 0
                }
            ],
            3: [
                {
                    "question": "Python can be used for:",
                    "options": ["Automation", "Only printing", "Only typing", "Only drawing"],
                    "answer": 0
                },
                {
                    "question": "Python can process:",
                    "options": ["Data", "Only paper", "Only cables", "Only monitors"],
                    "answer": 0
                },
                {
                    "question": "Python can be used in:",
                    "options": ["Web development", "Only hardware repair", "Only painting", "Only music playback"],
                    "answer": 0
                },
                {
                    "question": "Python can work with:",
                    "options": ["Files", "Only printers", "Only keyboards", "Only speakers"],
                    "answer": 0
                },
                {
                    "question": "Python is useful for:",
                    "options": ["Application development", "Only handwriting", "Only scanning", "Only printing"],
                    "answer": 0
                }
            ]
        }
    },

    "Database Systems": {
        "lessons": {
            1: {
                "title": "Lesson 1: Database Introduction",
                "content": """
                    <h3>Introduction to Database Systems</h3>
                    <p>
                        A database is an organized collection of data.
                        A database management system helps users store,
                        retrieve and manage that data.
                    </p>

                    <h4>Examples</h4>
                    <ul>
                        <li>Student records</li>
                        <li>Customer information</li>
                        <li>Product catalogs</li>
                        <li>Transaction records</li>
                    </ul>
                """
            },
            2: {
                "title": "Lesson 2: SQL Fundamentals",
                "content": """
                    <h3>SQL Fundamentals</h3>
                    <p>
                        SQL is used to communicate with relational
                        databases.
                    </p>

                    <h4>Common SQL Commands</h4>
                    <ul>
                        <li>SELECT</li>
                        <li>INSERT</li>
                        <li>UPDATE</li>
                        <li>DELETE</li>
                    </ul>
                """
            },
            3: {
                "title": "Lesson 3: Practical Database Applications",
                "content": """
                    <h3>Practical Database Applications</h3>
                    <p>
                        Databases are used by websites, business systems,
                        banking applications, education systems and many
                        other software applications.
                    </p>
                """
            }
        },

        "tests": {
            1: [
                {
                    "question": "What is a database?",
                    "options": [
                        "An organized collection of data",
                        "A keyboard",
                        "A monitor",
                        "A programming cable"
                    ],
                    "answer": 0
                },
                {
                    "question": "What does DBMS help users do?",
                    "options": [
                        "Manage data",
                        "Repair monitors",
                        "Print books",
                        "Design keyboards"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which is an example of stored database information?",
                    "options": [
                        "Student records",
                        "A desk lamp",
                        "A pencil",
                        "A chair"
                    ],
                    "answer": 0
                },
                {
                    "question": "Databases are commonly used to store:",
                    "options": [
                        "Structured information",
                        "Only paper",
                        "Only cables",
                        "Only images on walls"
                    ],
                    "answer": 0
                },
                {
                    "question": "A database helps organize:",
                    "options": [
                        "Data",
                        "Only hardware",
                        "Only electricity",
                        "Only furniture"
                    ],
                    "answer": 0
                }
            ],
            2: [
                {
                    "question": "What is SQL used for?",
                    "options": [
                        "Communicating with relational databases",
                        "Editing photos",
                        "Playing music",
                        "Operating a keyboard"
                    ],
                    "answer": 0
                },
                {
                    "question": "Which SQL command retrieves data?",
                    "options": ["SELECT", "INSERT", "DELETE", "UPDATE"],
                    "answer": 0
                },
                {
                    "question": "Which SQL command adds data?",
                    "options": ["INSERT", "SELECT", "DELETE", "UPDATE"],
                    "answer": 0
                },
                {
                    "question": "Which SQL command changes existing data?",
                    "options": ["UPDATE", "SELECT", "INSERT", "CREATE"],
                    "answer": 0
                },
                {
                    "question": "Which SQL command removes data?",
                    "options": ["DELETE", "SELECT", "INSERT", "UPDATE"],
                    "answer": 0
                }
            ],
            3: [
                {
                    "question": "Web applications commonly use:",
                    "options": ["Databases", "Only paper", "Only keyboards", "Only speakers"],
                    "answer": 0
                },
                {
                    "question": "Banking systems commonly store:",
                    "options": ["Transaction records", "Only pictures", "Only music", "Only fonts"],
                    "answer": 0
                },
                {
                    "question": "Education systems can use databases for:",
                    "options": ["Student records", "Only printing", "Only drawing", "Only audio"],
                    "answer": 0
                },
                {
                    "question": "Business systems can use databases for:",
                    "options": ["Customer information", "Only wallpapers", "Only cables", "Only monitors"],
                    "answer": 0
                },
                {
                    "question": "A database application normally helps users:",
                    "options": ["Store and retrieve information", "Only type letters", "Only print pages", "Only view videos"],
                    "answer": 0
                }
            ]
        }
    },

    "AWS Cloud Essentials": {
        "lessons": {
            1: {
                "title": "Lesson 1: AWS Introduction",
                "content": """
                    <h3>Introduction to AWS</h3>
                    <p>
                        Amazon Web Services (AWS) is a cloud platform
                        that provides computing, storage, database,
                        networking and other services.
                    </p>
                """
            },
            2: {
                "title": "Lesson 2: AWS Fundamentals",
                "content": """
                    <h3>AWS Fundamentals</h3>
                    <p>
                        AWS provides services such as EC2 for computing,
                        S3 for object storage and RDS for managed
                        relational databases.
                    </p>

                    <h4>Important Concepts</h4>
                    <ul>
                        <li>Regions</li>
                        <li>Availability Zones</li>
                        <li>Identity and Access Management</li>
                        <li>Elastic resources</li>
                    </ul>
                """
            },
            3: {
                "title": "Lesson 3: Practical AWS Applications",
                "content": """
                    <h3>Practical AWS Applications</h3>
                    <p>
                        AWS can host websites, APIs, databases, storage
                        systems, analytics workloads and enterprise
                        applications.
                    </p>
                """
            }
        },

        "tests": {
            1: [
                {
                    "question": "What is AWS?",
                    "options": [
                        "A cloud services platform",
                        "A word processor",
                        "A programming language",
                        "A keyboard"
                    ],
                    "answer": 0
                },
                {
                    "question": "AWS provides:",
                    "options": [
                        "Cloud computing services",
                        "Only printers",
                        "Only monitors",
                        "Only cables"
                    ],
                    "answer": 0
                },
                {
                    "question": "AWS can provide:",
                    "options": [
                        "Storage",
                        "Only paper",
                        "Only furniture",
                        "Only keyboards"
                    ],
                    "answer": 0
                },
                {
                    "question": "AWS can provide database services.",
                    "options": ["True", "False", "Only offline", "Never"],
                    "answer": 0
                },
                {
                    "question": "AWS is used over:",
                    "options": [
                        "Cloud infrastructure",
                        "Only a local keyboard",
                        "Only a printer",
                        "Only a calculator"
                    ],
                    "answer": 0
                }
            ],
            2: [
                {
                    "question": "Which AWS service provides virtual servers?",
                    "options": ["EC2", "S3", "RDS", "IAM"],
                    "answer": 0
                },
                {
                    "question": "Which AWS service provides object storage?",
                    "options": ["S3", "EC2", "RDS", "IAM"],
                    "answer": 0
                },
                {
                    "question": "Which AWS service is for managed relational databases?",
                    "options": ["RDS", "S3", "EC2", "IAM"],
                    "answer": 0
                },
                {
                    "question": "What is an AWS Region?",
                    "options": [
                        "A geographic area containing AWS infrastructure",
                        "A programming language",
                        "A database command",
                        "A local folder"
                    ],
                    "answer": 0
                },
                {
                    "question": "What does IAM help manage?",
                    "options": [
                        "Identity and access",
                        "Video playback",
                        "Keyboard layouts",
                        "Printer paper"
                    ],
                    "answer": 0
                }
            ],
            3: [
                {
                    "question": "AWS can be used to host:",
                    "options": ["Websites", "Only paper", "Only keyboards", "Only monitors"],
                    "answer": 0
                },
                {
                    "question": "AWS can host:",
                    "options": ["APIs", "Only printers", "Only pencils", "Only desks"],
                    "answer": 0
                },
                {
                    "question": "AWS can support:",
                    "options": ["Analytics workloads", "Only handwriting", "Only drawing", "Only furniture"],
                    "answer": 0
                },
                {
                    "question": "AWS can be used for enterprise:",
                    "options": ["Applications", "Only paper files", "Only speakers", "Only keyboards"],
                    "answer": 0
                },
                {
                    "question": "Cloud platforms can help applications:",
                    "options": [
                        "Scale and use managed infrastructure",
                        "Avoid all computing",
                        "Remove all storage",
                        "Work without software"
                    ],
                    "answer": 0
                }
            ]
        }
    }
}


# =========================================================
# FALLBACK FOR NEW COURSES
#
# If an admin creates another course, it gets content based
# on that course's name instead of accidentally showing
# Cloud Computing content.
#
# Replace this fallback with real content when you add a new
# course.
# =========================================================

def get_course_content(course_name):
    if course_name in COURSE_CONTENT:
        return COURSE_CONTENT[course_name]

    return {
        "lessons": {
            1: {
                "title": "Lesson 1: Introduction",
                "content": f"""
                    <h3>Introduction to {course_name}</h3>
                    <p>
                        This lesson introduces the main concepts,
                        terminology and purpose of {course_name}.
                    </p>
                """
            },
            2: {
                "title": "Lesson 2: Fundamentals",
                "content": f"""
                    <h3>{course_name} Fundamentals</h3>
                    <p>
                        This lesson covers the fundamental concepts
                        and principles of {course_name}.
                    </p>
                """
            },
            3: {
                "title": "Lesson 3: Practical Applications",
                "content": f"""
                    <h3>Practical Applications of {course_name}</h3>
                    <p>
                        This lesson explains practical uses of
                        {course_name}.
                    </p>
                """
            }
        },
        "tests": {
            1: [
                {
                    "question": f"What is an important topic in {course_name}?",
                    "options": [
                        f"Core concepts of {course_name}",
                        "A keyboard",
                        "A desk",
                        "A printer"
                    ],
                    "answer": 0
                }
            ],
            2: [
                {
                    "question": f"What should you learn in the fundamentals of {course_name}?",
                    "options": [
                        f"The fundamental concepts of {course_name}",
                        "Only hardware repair",
                        "Only printing",
                        "Only typing"
                    ],
                    "answer": 0
                }
            ],
            3: [
                {
                    "question": f"Where can {course_name} be applied?",
                    "options": [
                        "Real-world applications",
                        "Only on paper",
                        "Only on a keyboard",
                        "Nowhere"
                    ],
                    "answer": 0
                }
            ]
        }
    }


# =========================================================
# HELPERS
# =========================================================

def student_required():
    return session.get("role") == "student"


def get_course(course_id):
    conn = get_db()
    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()
    conn.close()
    return course


def lesson_completed(username, course_id, lesson_id):
    conn = get_db()
    row = conn.execute(
        """
        SELECT completed
        FROM lesson_progress
        WHERE username = ?
          AND course_id = ?
          AND lesson_id = ?
        """,
        (username, course_id, lesson_id)
    ).fetchone()
    conn.close()
    return bool(row and row["completed"])


def test_completed(username, course_id, lesson_id):
    conn = get_db()
    row = conn.execute(
        """
        SELECT *
        FROM test_results
        WHERE username = ?
          AND course_id = ?
          AND lesson_id = ?
        """,
        (username, course_id, lesson_id)
    ).fetchone()
    conn.close()
    return row


def course_completed(username, course_id):
    course = get_course(course_id)

    if course is None:
        return False

    content = get_course_content(course["name"])
    lesson_ids = sorted(content["lessons"].keys())

    for lesson_id in lesson_ids:
        if not lesson_completed(username, course_id, lesson_id):
            return False

        if not test_completed(username, course_id, lesson_id):
            return False

    return True


def can_access_lesson(username, course_id, lesson_id):
    course = get_course(course_id)

    if course is None:
        return False

    content = get_course_content(course["name"])
    lesson_ids = sorted(content["lessons"].keys())

    if lesson_id not in lesson_ids:
        return False

    # First lesson is always unlocked.
    if lesson_id == lesson_ids[0]:
        return True

    # Every later lesson requires the previous lesson's test.
    current_index = lesson_ids.index(lesson_id)
    previous_lesson_id = lesson_ids[current_index - 1]

    return test_completed(
        username,
        course_id,
        previous_lesson_id
    ) is not None


# =========================================================
# HOME / LOGIN / LOGOUT
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            # Clear any previous/stale session
            session.clear()

            # Create a fresh session for the logged-in user
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("student"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student")
def student():
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]

    conn = get_db()

    courses = conn.execute(
        "SELECT * FROM courses"
    ).fetchall()

    materials = conn.execute(
        "SELECT * FROM materials"
    ).fetchall()

    results = conn.execute(
        """
        SELECT *
        FROM results
        WHERE username = ?
        """,
        (username,)
    ).fetchall()

    conn.close()

    course_progress = []

    for course in courses:
        content = get_course_content(course["name"])
        lesson_ids = sorted(content["lessons"].keys())

        completed_lessons = 0
        completed_tests = 0

        for lesson_id in lesson_ids:
            if lesson_completed(username, course["id"], lesson_id):
                completed_lessons += 1

            if test_completed(username, course["id"], lesson_id):
                completed_tests += 1

        course_progress.append({
            "course": course,
            "completed_lessons": completed_lessons,
            "completed_tests": completed_tests,
            "total_lessons": len(lesson_ids),
            "completed": (
                completed_lessons == len(lesson_ids)
                and completed_tests == len(lesson_ids)
            )
        })

    return render_template(
        "student.html",
        courses=courses,
        materials=materials,
        results=results,
        course_progress=course_progress
    )


# =========================================================
# COURSE DETAILS
# =========================================================

@app.route("/course/<int:course_id>")
def course_details(course_id):
    if "username" not in session:
        return redirect(url_for("login"))

    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    return render_template(
        "course.html",
        course=course
    )


# =========================================================
# COURSE LEARNING MODULE
# =========================================================

@app.route("/course/<int:course_id>/learn")
def course_learn(course_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    content = get_course_content(course["name"])
    lesson_ids = sorted(content["lessons"].keys())

    progress = []

    for lesson_id in lesson_ids:
        completed = lesson_completed(
            username,
            course_id,
            lesson_id
        )

        test = test_completed(
            username,
            course_id,
            lesson_id
        )

        progress.append({
            "lesson_id": lesson_id,
            "title": content["lessons"][lesson_id]["title"],
            "completed": completed,
            "test_completed": test is not None,
            "test": test,
            "unlocked": can_access_lesson(
                username,
                course_id,
                lesson_id
            )
        })

    completed_lessons = sum(
        1 for item in progress
        if item["completed"]
    )

    completed_tests = sum(
        1 for item in progress
        if item["test_completed"]
    )

    completed = course_completed(
        username,
        course_id
    )

    return render_template(
        "learn.html",
        course=course,
        progress=progress,
        completed_lessons=completed_lessons,
        completed_tests=completed_tests,
        course_completed=completed
    )


# =========================================================
# LESSON
# =========================================================

@app.route("/course/<int:course_id>/learn/<int:lesson_id>")
def lesson(course_id, lesson_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    content = get_course_content(course["name"])

    if lesson_id not in content["lessons"]:
        return "Lesson not found", 404

    if not can_access_lesson(
        username,
        course_id,
        lesson_id
    ):
        flash("Complete the previous lesson and test first.")
        return redirect(
            url_for(
                "course_learn",
                course_id=course_id
            )
        )

    completed = lesson_completed(
        username,
        course_id,
        lesson_id
    )

    test = test_completed(
        username,
        course_id,
        lesson_id
    )

    return render_template(
        "lesson.html",
        course=course,
        lesson=content["lessons"][lesson_id],
        lesson_id=lesson_id,
        completed=completed,
        test_completed=test is not None,
        test_result=test
    )


# =========================================================
# COMPLETE LESSON
# =========================================================

@app.route(
    "/course/<int:course_id>/learn/<int:lesson_id>/complete",
    methods=["POST"]
)
def complete_lesson(course_id, lesson_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    content = get_course_content(course["name"])

    if lesson_id not in content["lessons"]:
        return "Lesson not found", 404

    if not can_access_lesson(
        username,
        course_id,
        lesson_id
    ):
        flash("This lesson is locked.")
        return redirect(
            url_for(
                "course_learn",
                course_id=course_id
            )
        )

    conn = get_db()

    conn.execute(
        """
        INSERT INTO lesson_progress(
            username,
            course_id,
            lesson_id,
            completed
        )
        VALUES (?, ?, ?, 1)
        ON CONFLICT(
            username,
            course_id,
            lesson_id
        )
        DO UPDATE SET completed = 1
        """,
        (
            username,
            course_id,
            lesson_id
        )
    )

    conn.commit()
    conn.close()

    flash("Lesson completed! Your test is now available.")

    return redirect(
        url_for(
            "take_test",
            course_id=course_id,
            lesson_id=lesson_id
        )
    )


# =========================================================
# TAKE TEST
# =========================================================

@app.route(
    "/course/<int:course_id>/test/<int:lesson_id>",
    methods=["GET", "POST"]
)
def take_test(course_id, lesson_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    content = get_course_content(course["name"])
    tests = content["tests"]

    if lesson_id not in tests:
        return "Test not found", 404

    if not lesson_completed(
        username,
        course_id,
        lesson_id
    ):
        flash("Complete the lesson before taking the test.")
        return redirect(
            url_for(
                "lesson",
                course_id=course_id,
                lesson_id=lesson_id
            )
        )

    existing_result = test_completed(
        username,
        course_id,
        lesson_id
    )

    if existing_result:
        return render_template(
            "test_result.html",
            course=course,
            lesson_id=lesson_id,
            result=existing_result
        )

    if request.method == "POST":
        questions = tests[lesson_id]
        score = 0

        for index, question in enumerate(questions):
            answer = request.form.get(
                f"question_{index}"
            )

            if answer is None:
                continue

            try:
                selected_answer = int(answer)
            except ValueError:
                continue

            if selected_answer == question["answer"]:
                score += 1

        total = len(questions)
        percentage = int((score / total) * 100) if total else 0

        conn = get_db()

        conn.execute(
            """
            INSERT INTO test_results(
                username,
                course_id,
                lesson_id,
                score,
                total,
                percentage
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                course_id,
                lesson_id,
                score,
                total,
                percentage
            )
        )

        # Recalculate the student's result for this course only.
        test_rows = conn.execute(
            """
            SELECT percentage
            FROM test_results
            WHERE username = ?
              AND course_id = ?
            """,
            (
                username,
                course_id
            )
        ).fetchall()

        overall = int(
            sum(row["percentage"] for row in test_rows)
            / len(test_rows)
        ) if test_rows else 0

        # Remove only this student's result for this course.
        conn.execute(
            """
            DELETE FROM results
            WHERE username = ?
              AND course = ?
            """,
            (
                username,
                course["name"]
            )
        )

        conn.execute(
            """
            INSERT INTO results(
                username,
                course,
                mark
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                course["name"],
                overall
            )
        )

        conn.commit()
        conn.close()

        if course_completed(
            username,
            course_id
        ):
            flash("🎉 Congratulations! You completed the course!")

            return redirect(
                url_for(
                    "course_completed_page",
                    course_id=course_id
                )
            )

        return redirect(
            url_for(
                "test_result",
                course_id=course_id,
                lesson_id=lesson_id
            )
        )

    return render_template(
        "test.html",
        course=course,
        lesson_id=lesson_id,
        questions=tests[lesson_id]
    )


# =========================================================
# TEST RESULT
# =========================================================

@app.route(
    "/course/<int:course_id>/test/<int:lesson_id>/result"
)
def test_result(course_id, lesson_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    result = test_completed(
        username,
        course_id,
        lesson_id
    )

    if result is None:
        return redirect(
            url_for(
                "take_test",
                course_id=course_id,
                lesson_id=lesson_id
            )
        )

    return render_template(
        "test_result.html",
        course=course,
        lesson_id=lesson_id,
        result=result
    )


# =========================================================
# COURSE COMPLETED
# =========================================================

@app.route("/course/<int:course_id>/completed")
def course_completed_page(course_id):
    if not student_required():
        return redirect(url_for("login"))

    username = session["username"]
    course = get_course(course_id)

    if course is None:
        return "Course not found", 404

    if not course_completed(
        username,
        course_id
    ):
        return redirect(
            url_for(
                "course_learn",
                course_id=course_id
            )
        )

    conn = get_db()

    test_results = conn.execute(
        """
        SELECT *
        FROM test_results
        WHERE username = ?
          AND course_id = ?
        ORDER BY lesson_id
        """,
        (
            username,
            course_id
        )
    ).fetchall()

    conn.close()

    overall = int(
        sum(result["percentage"] for result in test_results)
        / len(test_results)
    ) if test_results else 0

    return render_template(
        "course_completed.html",
        course=course,
        test_results=test_results,
        overall=overall
    )


# =========================================================
# ADMIN
# =========================================================

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    courses = conn.execute(
        "SELECT * FROM courses"
    ).fetchall()

    materials = conn.execute(
        "SELECT * FROM materials"
    ).fetchall()

    results = conn.execute(
        "SELECT * FROM results"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        courses=courses,
        materials=materials,
        results=results
    )


@app.route(
    "/admin/course",
    methods=["POST"]
)
def add_course():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    name = request.form["name"].strip()
    description = request.form["description"].strip()

    conn = get_db()

    conn.execute(
        """
        INSERT INTO courses(name, description)
        VALUES (?, ?)
        """,
        (
            name,
            description
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/admin/material", methods=["POST"])

def add_material():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    link = request.form["link"].strip()

    conn = get_db()

    conn.execute(
        """
        INSERT INTO materials(title, link)
        VALUES (?, ?)
        """,
        (
            title,
            link
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))

# =========================================================
# DELETE LEARNING MATERIAL
# =========================================================

@app.route("/admin/material/delete/<int:material_id>", methods=["POST"])
def delete_material(material_id):

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    material = conn.execute(
        """
        SELECT *
        FROM materials
        WHERE id = ?
        """,
        (material_id,)
    ).fetchone()

    if material is None:
        conn.close()
        flash("Learning material not found.")
        return redirect(url_for("admin"))

    conn.execute(
        """
        DELETE FROM materials
        WHERE id = ?
        """,
        (material_id,)
    )

    conn.commit()
    conn.close()

    flash(f'Learning material "{material["title"]}" was deleted successfully.')

    return redirect(url_for("admin"))

@app.route(
    "/admin/result",
    methods=["POST"]
)
def add_result():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    username = request.form["username"].strip()
    course = request.form["course"].strip()
    mark = request.form["mark"].strip()

    conn = get_db()

    conn.execute(
        """
        INSERT INTO results(username, course, mark)
        VALUES (?, ?, ?)
        """,
        (
            username,
            course,
            mark
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
