-- Disable autocommit, abort if something goes wrong
SET autocommit off;
-- WHENEVER sqlerror EXIT FAILURE ROLLBACK;
SET serveroutput on;

ALTER TABLE param_definition ADD activation VARCHAR2(10 CHAR);
ALTER TABLE param_definition DROP COLUMN rebuild_required;
QUIT;
