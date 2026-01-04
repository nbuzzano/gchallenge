-- Number of employees hired for each job and department in 2021 divided by quarter
-- Ordered alphabetically by department and job
-- Uses string functions for compatibility with SQLite and PostgreSQL

SELECT 
    d.department,
    j.job,
    SUM(CASE WHEN SUBSTR(e.datetime, 6, 2) IN ('01', '02', '03') THEN 1 ELSE 0 END) AS Q1,
    SUM(CASE WHEN SUBSTR(e.datetime, 6, 2) IN ('04', '05', '06') THEN 1 ELSE 0 END) AS Q2,
    SUM(CASE WHEN SUBSTR(e.datetime, 6, 2) IN ('07', '08', '09') THEN 1 ELSE 0 END) AS Q3,
    SUM(CASE WHEN SUBSTR(e.datetime, 6, 2) IN ('10', '11', '12') THEN 1 ELSE 0 END) AS Q4
FROM employees e
JOIN departments d ON e.department_id = d.id
JOIN jobs j ON e.job_id = j.id
WHERE SUBSTR(e.datetime, 1, 4) = '2021'
GROUP BY d.department, j.job
ORDER BY d.department ASC, j.job ASC;
