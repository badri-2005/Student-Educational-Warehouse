-- ============================================================
-- schema.sql
-- Educational Data Warehouse - Star Schema (MySQL 8)
-- ============================================================

CREATE DATABASE IF NOT EXISTS edu_dw
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE edu_dw;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- dim_student : SCD Type 2
-- Grain: one row per version of a student's tracked attributes.
-- When department (or another tracked attribute) changes, the old
-- row is expired (is_current = FALSE, expiry_date set) and a new
-- row is inserted with a new surrogate key.
DROP TABLE IF EXISTS dim_student;
CREATE TABLE dim_student (
    student_key         BIGINT AUTO_INCREMENT PRIMARY KEY,   -- surrogate key
    student_id          VARCHAR(20)   NOT NULL,               -- natural/business key
    student_name        VARCHAR(150)  NOT NULL,
    gender              VARCHAR(10),
    date_of_birth       DATE,
    department          VARCHAR(20)   NOT NULL,
    admission_year      INT,
    entrance_score_band VARCHAR(10),
    effective_date      DATE          NOT NULL,
    expiry_date         DATE          NULL,
    is_current          BOOLEAN       NOT NULL DEFAULT TRUE,
    INDEX idx_dim_student_natural (student_id),
    INDEX idx_dim_student_current (student_id, is_current)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS dim_course;
CREATE TABLE dim_course (
    course_key      BIGINT AUTO_INCREMENT PRIMARY KEY,
    course_id       VARCHAR(20)  NOT NULL UNIQUE,
    course_name     VARCHAR(150) NOT NULL,
    department      VARCHAR(20)  NOT NULL
) ENGINE=InnoDB;

DROP TABLE IF EXISTS dim_department;
CREATE TABLE dim_department (
    department_key   BIGINT AUTO_INCREMENT PRIMARY KEY,
    department_id    VARCHAR(20)  NOT NULL UNIQUE,
    department_name  VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

DROP TABLE IF EXISTS dim_semester;
CREATE TABLE dim_semester (
    semester_key     BIGINT AUTO_INCREMENT PRIMARY KEY,
    semester_number  INT NOT NULL UNIQUE,
    academic_year    VARCHAR(20)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key    BIGINT PRIMARY KEY,   -- YYYYMMDD integer
    full_date   DATE NOT NULL UNIQUE,
    day         INT,
    month       INT,
    quarter     INT,
    year        INT
) ENGINE=InnoDB;

-- ============================================================
-- FACT TABLES
-- ============================================================

-- fact_attendance
-- Grain: one row per student-course-semester attendance record.
DROP TABLE IF EXISTS fact_attendance;
CREATE TABLE fact_attendance (
    attendance_key       BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_key           BIGINT NOT NULL,
    course_key             BIGINT NOT NULL,
    semester_key           BIGINT NOT NULL,
    total_classes           INT NOT NULL,
    attended_classes        INT NOT NULL,
    attendance_percentage   DECIMAL(5,2) NOT NULL,
    CONSTRAINT fk_att_student  FOREIGN KEY (student_key)  REFERENCES dim_student(student_key),
    CONSTRAINT fk_att_course   FOREIGN KEY (course_key)   REFERENCES dim_course(course_key),
    CONSTRAINT fk_att_semester FOREIGN KEY (semester_key) REFERENCES dim_semester(semester_key),
    INDEX idx_fact_att_student (student_key),
    INDEX idx_fact_att_course (course_key)
) ENGINE=InnoDB;

-- fact_assessment
-- Grain: one row per student-course-semester assessment record.
DROP TABLE IF EXISTS fact_assessment;
CREATE TABLE fact_assessment (
    assessment_key   BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_key       BIGINT NOT NULL,
    course_key         BIGINT NOT NULL,
    semester_key       BIGINT NOT NULL,
    internal_marks       DECIMAL(5,2),
    assignment_marks     DECIMAL(5,2),
    quiz_marks           DECIMAL(5,2),
    lab_marks            DECIMAL(5,2),
    final_marks          DECIMAL(5,2),
    CONSTRAINT fk_asm_student  FOREIGN KEY (student_key)  REFERENCES dim_student(student_key),
    CONSTRAINT fk_asm_course   FOREIGN KEY (course_key)   REFERENCES dim_course(course_key),
    CONSTRAINT fk_asm_semester FOREIGN KEY (semester_key) REFERENCES dim_semester(semester_key),
    INDEX idx_fact_asm_student (student_key),
    INDEX idx_fact_asm_course (course_key)
) ENGINE=InnoDB;

-- fact_academic_performance
-- Grain: one row per student-semester performance summary.
DROP TABLE IF EXISTS fact_academic_performance;
CREATE TABLE fact_academic_performance (
    performance_key   BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_key         BIGINT NOT NULL,
    semester_key         BIGINT NOT NULL,
    gpa                    DECIMAL(4,2),
    cgpa                   DECIMAL(4,2),
    backlogs                INT DEFAULT 0,
    pass_fail                VARCHAR(10),
    academic_status            VARCHAR(20),
    CONSTRAINT fk_perf_student  FOREIGN KEY (student_key)  REFERENCES dim_student(student_key),
    CONSTRAINT fk_perf_semester FOREIGN KEY (semester_key) REFERENCES dim_semester(semester_key),
    INDEX idx_fact_perf_student (student_key)
) ENGINE=InnoDB;

-- fact_lms_activity
-- Grain: one row per student-course-semester LMS activity record.
DROP TABLE IF EXISTS fact_lms_activity;
CREATE TABLE fact_lms_activity (
    lms_key             BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_key           BIGINT NOT NULL,
    course_key             BIGINT NOT NULL,
    semester_key           BIGINT NOT NULL,
    login_count               INT,
    content_views              INT,
    assignment_submission_rate  DECIMAL(5,2),
    average_session_minutes       DECIMAL(6,2),
    CONSTRAINT fk_lms_student  FOREIGN KEY (student_key)  REFERENCES dim_student(student_key),
    CONSTRAINT fk_lms_course   FOREIGN KEY (course_key)   REFERENCES dim_course(course_key),
    CONSTRAINT fk_lms_semester FOREIGN KEY (semester_key) REFERENCES dim_semester(semester_key),
    INDEX idx_fact_lms_student (student_key),
    INDEX idx_fact_lms_course (course_key)
) ENGINE=InnoDB;

-- ============================================================
-- SCD TYPE 2 DEMONSTRATION (run manually to show the mechanism)
-- Example: student STU00001 transfers from CSE to IT
-- ============================================================
-- Step 1: expire the current row
-- UPDATE dim_student
-- SET is_current = FALSE, expiry_date = CURDATE()
-- WHERE student_id = 'STU00001' AND is_current = TRUE;
--
-- Step 2: insert the new version
-- INSERT INTO dim_student
--   (student_id, student_name, gender, date_of_birth, department,
--    admission_year, entrance_score_band, effective_date, expiry_date, is_current)
-- SELECT student_id, student_name, gender, date_of_birth, 'IT',
--        admission_year, entrance_score_band, CURDATE(), NULL, TRUE
-- FROM dim_student
-- WHERE student_id = 'STU00001' AND is_current = FALSE
-- ORDER BY student_key DESC LIMIT 1;
--
-- Old fact rows still reference the OLD student_key (CSE version);
-- new fact rows going forward will reference the NEW student_key (IT version).
-- This is exactly what preserves history in SCD Type 2.
