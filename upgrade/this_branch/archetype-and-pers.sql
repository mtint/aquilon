
ALTER TABLE PERSONALITY ADD "CLUSTER_REQUIRED" NUMBER(*,0);
UPDATE PERSONALITY SET CLUSTER_REQUIRED=(SELECT CLUSTER_REQUIRED FROM ARCHETYPE WHERE ARCHETYPE.ID = PERSONALITY.ID);
ALTER TABLE PERSONALITY ADD CONSTRAINT "PERSONALITY_CLSTR_REQ_CK" CHECK (CLUSTER_REQUIRED IN (0, 1)) ENABLE;

ALTER TABLE ARCHETYPE ADD "CLUSTER_TYPE" VARCHAR(32) NULL;
ALTER TABLE ARCHETYPE ADD "OUTPUTDESC" VARCHAR(255) NULL;
ALTER TABLE ARCHETYPE DROP CONSTRAINT "ARCHETYPE_CLUSTER_REQUIRED_CK";
ALTER TABLE ARCHETYPE DROP CONSTRAINT "ARCHETYPE_CLUSTER_REQUIRED_NN";
ALTER TABLE ARCHETYPE DROP COLUMN CLUSTER_REQUIRED;

COMMIT;
