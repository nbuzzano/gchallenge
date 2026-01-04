-- List of departments that hired more employees than the mean in 2021
-- Ordered by number of employees hired (descending)
-- Uses subquery approach for compatibility with SQLite and PostgreSQL

WITH dept_hires AS (
    SELECT 
        d.id,
        d.department,
        COUNT(e.id) as hired
    FROM departments d
    LEFT JOIN employees e ON d.id = e.department_id
        AND SUBSTR(e.datetime, 1, 4) = '2021'
    GROUP BY d.id, d.department
),
avg_hires AS (
    SELECT AVG(hired) as mean_hired
    FROM dept_hires
)
SELECT 
    dh.id,
    dh.department,
    dh.hired
FROM dept_hires dh
CROSS JOIN avg_hires ah
WHERE dh.hired > ah.mean_hired
ORDER BY dh.hired DESC;
