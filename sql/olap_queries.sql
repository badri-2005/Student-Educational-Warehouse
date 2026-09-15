-- ============================================================
-- olap_queries.sql
-- OLAP operations against the star schema in edu_dw.
-- Each query is commented with what OLAP concept it demonstrates.
-- ============================================================

USE edu_dw;

-- ------------------------------------------------------------
-- 1) ROLL-UP: Student -> Department -> College
-- Aggregating GPA upward from individual student to department to
-- the whole college (grand total).
-- ------------------------------------------------------------
SELECT
    ds.department,
    AVG(fp.gpa) AS avg_gpa_department
FROM fact_academic_performance fp
JOIN dim_student ds ON fp.student_key = ds.student_key AND ds.is_current = TRUE
GROUP BY ds.department WITH ROLLUP;
-- The WITH ROLLUP row where department is NULL is the college-wide grand total.

-- ------------------------------------------------------------
-- 2) DRILL-DOWN: Department -> Course -> Student
-- Starting from a department-level view and drilling into course-level
-- and then student-level detail for the CSE department.
-- ------------------------------------------------------------
SELECT
    ds.department,
    dc.course_id,
    dc.course_name,
    ds.student_id,
    ds.student_name,
    fa.internal_marks,
    fa.final_marks
FROM fact_assessment fa
JOIN dim_student ds ON fa.student_key = ds.student_key AND ds.is_current = TRUE
JOIN dim_course dc  ON fa.course_key = dc.course_key
WHERE ds.department = 'CSE'
ORDER BY dc.course_id, ds.student_id;

-- ------------------------------------------------------------
-- 3) SLICE: Fix one dimension (semester = 3), analyze across others.
-- ------------------------------------------------------------
SELECT
    ds.department,
    dc.course_name,
    AVG(fa.final_marks) AS avg_final_marks
FROM fact_assessment fa
JOIN dim_student ds  ON fa.student_key = ds.student_key AND ds.is_current = TRUE
JOIN dim_course dc   ON fa.course_key = dc.course_key
JOIN dim_semester dsem ON fa.semester_key = dsem.semester_key
WHERE dsem.semester_number = 3
GROUP BY ds.department, dc.course_name;

-- ------------------------------------------------------------
-- 4) DICE: Multiple filters at once
-- Department = CSE AND Semester = 5 AND attendance < 75%
-- ------------------------------------------------------------
SELECT
    ds.student_id,
    ds.student_name,
    dc.course_name,
    fat.attendance_percentage
FROM fact_attendance fat
JOIN dim_student ds    ON fat.student_key = ds.student_key AND ds.is_current = TRUE
JOIN dim_course dc     ON fat.course_key = dc.course_key
JOIN dim_semester dsem ON fat.semester_key = dsem.semester_key
WHERE ds.department = 'CSE'
  AND dsem.semester_number = 5
  AND fat.attendance_percentage < 75;

-- ------------------------------------------------------------
-- 5) PIVOT: Course performance across semesters
-- (MySQL has no native PIVOT, so conditional aggregation is used)
-- ------------------------------------------------------------
SELECT
    dc.course_name,
    AVG(CASE WHEN dsem.semester_number = 1 THEN fa.final_marks END) AS sem1_avg,
    AVG(CASE WHEN dsem.semester_number = 2 THEN fa.final_marks END) AS sem2_avg,
    AVG(CASE WHEN dsem.semester_number = 3 THEN fa.final_marks END) AS sem3_avg,
    AVG(CASE WHEN dsem.semester_number = 4 THEN fa.final_marks END) AS sem4_avg,
    AVG(CASE WHEN dsem.semester_number = 5 THEN fa.final_marks END) AS sem5_avg,
    AVG(CASE WHEN dsem.semester_number = 6 THEN fa.final_marks END) AS sem6_avg
FROM fact_assessment fa
JOIN dim_course dc     ON fa.course_key = dc.course_key
JOIN dim_semester dsem ON fa.semester_key = dsem.semester_key
GROUP BY dc.course_name;

-- ------------------------------------------------------------
-- 6) Average GPA by department
-- ------------------------------------------------------------
SELECT ds.department, ROUND(AVG(fp.gpa), 2) AS avg_gpa
FROM fact_academic_performance fp
JOIN dim_student ds ON fp.student_key = ds.student_key AND ds.is_current = TRUE
GROUP BY ds.department
ORDER BY avg_gpa DESC;

-- ------------------------------------------------------------
-- 7) Average attendance by semester
-- ------------------------------------------------------------
SELECT dsem.semester_number, ROUND(AVG(fat.attendance_percentage), 2) AS avg_attendance
FROM fact_attendance fat
JOIN dim_semester dsem ON fat.semester_key = dsem.semester_key
GROUP BY dsem.semester_number
ORDER BY dsem.semester_number;

-- ------------------------------------------------------------
-- 8) Pass percentage by course
-- ------------------------------------------------------------
SELECT
    dc.course_name,
    ROUND(100 * SUM(CASE WHEN fa.final_marks >= 40 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pass_percentage
FROM fact_assessment fa
JOIN dim_course dc ON fa.course_key = dc.course_key
GROUP BY dc.course_name
ORDER BY pass_percentage DESC;

-- ------------------------------------------------------------
-- 9) Students at risk by department (academic_status = 'AT_RISK')
-- ------------------------------------------------------------
SELECT ds.department, COUNT(DISTINCT ds.student_id) AS at_risk_students
FROM fact_academic_performance fp
JOIN dim_student ds ON fp.student_key = ds.student_key AND ds.is_current = TRUE
WHERE fp.academic_status = 'AT_RISK'
GROUP BY ds.department
ORDER BY at_risk_students DESC;

-- ------------------------------------------------------------
-- 10) Average marks by subject (course)
-- ------------------------------------------------------------
SELECT
    dc.course_name,
    ROUND(AVG(fa.internal_marks), 2) AS avg_internal,
    ROUND(AVG(fa.final_marks), 2) AS avg_final
FROM fact_assessment fa
JOIN dim_course dc ON fa.course_key = dc.course_key
GROUP BY dc.course_name
ORDER BY avg_final DESC;

-- ------------------------------------------------------------
-- 11) LMS activity vs academic performance
-- Correlating engagement (login_count) with GPA at student level.
-- ------------------------------------------------------------
SELECT
    ds.student_id,
    ROUND(AVG(fl.login_count), 1) AS avg_logins,
    ROUND(AVG(fp.gpa), 2) AS avg_gpa
FROM fact_lms_activity fl
JOIN dim_student ds ON fl.student_key = ds.student_key AND ds.is_current = TRUE
JOIN fact_academic_performance fp ON fp.student_key = ds.student_key
GROUP BY ds.student_id
ORDER BY avg_gpa DESC
LIMIT 50;
