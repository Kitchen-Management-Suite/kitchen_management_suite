-- Created by Rohan Plante
-- 11/20/2025
-- gets user emails for users who are:
--    1. have authored multiple recipes
--    2. are members of multiple households
--    3. are an admin in at least one of those households
SELECT    DISTINCT "Email", "HouseholdName", "RoleName"
FROM      public."Users" AS U
JOIN      public."Members" AS M USING ("UserID")
JOIN      public."Households" AS H USING ("HouseholdID")
JOIN      public."Authors" AS A USING ("UserID")
JOIN      public."Roles" AS R USING ("RoleID")
WHERE     1 < (
          SELECT    COUNT(*)
          FROM      public."Authors" AS A1
          WHERE     A1."UserID" = U."UserID"
          )
AND       1 < (
          SELECT    COUNT(*)
          FROM      public."Members" AS M1
          WHERE     M1."UserID" = U."UserID"
          )
AND       "RoleName" = 'admin'
GROUP BY  "Email", "HouseholdName", "RoleName"