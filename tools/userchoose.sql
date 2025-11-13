SELECT DISTINCT
  U."FirstName",
  U."LastName",
  U."Email"
FROM
  public."Users" AS U,
  public."Members" AS M,
  public."Authors" AS A
WHERE
  1 < (
    SELECT
      COUNT()
    FROM
      public."Members" AS M1
    WHERE
      M1."UserID" = M."UserID"
  )
  AND A."UserID" = M."UserID"
  AND U."UserID" = M."UserID"
  AND 1 < (
    SELECT
      COUNT()
    FROM
      public."Authors" AS A1
    WHERE
      A1."UserID" = A."UserID"
  )
GROUP BY
  U."FirstName",
  U."LastName",
  U."Email";
