-- ============================================================
-- staging.sql
-- Staging tables: near-raw landing zone for CSV data before
-- cleaning/transformation and loading into the star schema.
-- ============================================================

USE edu_dw;

DROP TABLE IF EXISTS stg_students;
CREATE TABLE stg_students (
    student_id          VARCHAR(20),
    name                VARCHAR(150),
    gender              VARCHAR(10),
    date_of_birth       VARCHAR(20),
    department           VARCHAR(20),
    admission_year        INT,
    entrance_score_band     VARCHAR(10)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS stg_course_enrollment;
CREATE TABLE stg_course_enrollment (
    student_id   VARCHAR(20),
    course_id     VARCHAR(20),
    course_name    VARCHAR(150),
    department       VARCHAR(20),
    semester           INT
) ENGINE=InnoDB;

DROP TABLE IF EXISTS stg_attendance;
CREATE TABLE stg_attendance (
    student_id       VARCHAR(20),
    course_id         VARCHAR(20),
    semester            INT,
    total_classes          INT,
    attended_classes          INT,
    attendance_percentage        DECIMAL(6,2)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS stg_assessments;
CREATE TABLE stg_assessments (
    student_id     VARCHAR(20),
    course_id       VARCHAR(20),
    semester           INT,
    internal_marks         DECIMAL(6,2),
    assignment_marks          DECIMAL(6,2),
    quiz_marks                    DECIMAL(6,2),
    lab_marks                        DECIMAL(6,2),
    final_marks                         DECIMAL(6,2)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS stg_lms_activity;
CREATE TABLE stg_lms_activity (
    student_id     VARCHAR(20),
    course_id       VARCHAR(20),
    semester           INT,
    login_count            INT,
    content_views              INT,
    assignment_submission_rate    DECIMAL(6,2),
    average_session_minutes          DECIMAL(6,2)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS stg_academic_performance;
CREATE TABLE stg_academic_performance (
    student_id   VARCHAR(20),
    semester       INT,
    gpa               DECIMAL(6,2),
    cgpa                 DECIMAL(6,2),
    backlogs                INT,
    pass_fail                  VARCHAR(10),
    academic_status               VARCHAR(20)
) ENGINE=InnoDB;
