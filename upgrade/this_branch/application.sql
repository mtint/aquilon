ALTER TABLE application RENAME COLUMN eonid TO eon_id;
ALTER TABLE application ADD CONSTRAINT application_grn_fk FOREIGN KEY (eon_id) REFERENCES grn (eon_id);

QUIT;
