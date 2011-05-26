
CREATE TABLE "RESHOLDER"
 (   "ID" NUMBER(*,0) CONSTRAINT "RESHOLDER_ID_NN" NOT NULL ENABLE,
     "CLUSTER_ID" NUMBER(*,0),
     "HOLDER_TYPE" VARCHAR2(16 CHAR) CONSTRAINT "RESHOLDER_HOLDER_TYPE_NN" NOT NULL ENABLE,
     "HOST_ID" NUMBER(*,0),
      CONSTRAINT "RESHOLDER_CLSTR_FK" FOREIGN KEY ("CLUSTER_ID") REFERENCES "CLSTR" ("ID") ON DELETE CASCADE ENABLE,
      CONSTRAINT "RESHOLDER_HOST_FK" FOREIGN KEY ("HOST_ID") REFERENCES "HOST" ("MACHINE_ID") ON DELETE CASCADE ENABLE,
      CONSTRAINT "RESHOLDER_PK" PRIMARY KEY ("ID") ENABLE
 );


CREATE TABLE "resource"
 (   "ID" NUMBER(*,0) CONSTRAINT "resource_ID_NN" NOT NULL ENABLE,
     "COMMENTS" VARCHAR2(255 CHAR),
     "CREATION_DATE" DATE CONSTRAINT "resource_CR_DATE_NN" NOT NULL ENABLE,
     "HOLDER_ID" NUMBER(*,0),
     "NAME" VARCHAR2(64 CHAR) CONSTRAINT "resource_NAME_NN" NOT NULL ENABLE,
     "RESOURCE_TYPE" VARCHAR2(16 CHAR) CONSTRAINT "resource_RESOURCE_TYPE_NN" NOT NULL ENABLE,
      PRIMARY KEY ("ID") ENABLE,
      CONSTRAINT "RESOURCE_RESHOLDER_FK" FOREIGN KEY ("HOLDER_ID") REFERENCES "RESHOLDER" ("ID") ON DELETE CASCADE ENABLE
 );


CREATE TABLE "FILESYSTEM"
 (   "ID" NUMBER(*,0) CONSTRAINT "FILESYSTEM_ID_NN" NOT NULL ENABLE,
     "BLOCKDEV" VARCHAR2(255 CHAR) CONSTRAINT "FILESYSTEM_BLOCKDEV_NN" NOT NULL ENABLE,
     "DUMPFREQ" NUMBER(*,0),
     "FSTYPE" VARCHAR2(32 CHAR) CONSTRAINT "FILESYSTEM_FSTYPE_NN" NOT NULL ENABLE,
     "MOUNT" NUMBER(*,0) CONSTRAINT "FILESYSTEM_MOUNT_NN" NOT NULL ENABLE,
     "MOUNTOPTIONS" VARCHAR2(255 CHAR),
     "MOUNTPOINT" VARCHAR2(255 CHAR) CONSTRAINT "FILESYSTEM_MOUNTPOINT_NN" NOT NULL ENABLE,
     "PASSNO" NUMBER(*,0),
      CONSTRAINT "FILESYSTEM_MOUNT_CK" CHECK (mount IN (0, 1)) ENABLE,
      CONSTRAINT "FILESYSTEM_PK" PRIMARY KEY ("ID") ENABLE,
      CONSTRAINT "FS_RESOURCE_FK" FOREIGN KEY ("ID") REFERENCES "resource" ("ID") ON DELETE CASCADE ENABLE
 );


CREATE TABLE "APPLICATION"
 (   "ID" NUMBER(*,0) CONSTRAINT "APPLICATION_ID_NN" NOT NULL ENABLE,
     "EONID" NUMBER(*,0) CONSTRAINT "APPLICATION_EONID_NN" NOT NULL ENABLE,
      CONSTRAINT "APPLICATION_PK" PRIMARY KEY ("ID") ENABLE,
      CONSTRAINT "APP_RESOURCE_FK" FOREIGN KEY ("ID") REFERENCES "resource" ("ID") ON DELETE CASCADE ENABLE
 );

CREATE TABLE "INTERVENTION"
 (   "ID" NUMBER(*,0) CONSTRAINT "INTERVENTION_ID_NN" NOT NULL ENABLE,
     "DISABLED" VARCHAR2(255 CHAR),
     "ENABLED" VARCHAR2(255 CHAR),
     "EXPIRY_DATE" DATE CONSTRAINT "INTERVENTION_EXPIRY_DATE_NN" NOT NULL ENABLE,
     "START_DATE" DATE CONSTRAINT "INTERVENTION_START_DATE_NN" NOT NULL ENABLE,
     "GROUPS" VARCHAR2(255 CHAR),
     "JUSTIFICATION" VARCHAR2(255 CHAR),
     "USERS" VARCHAR2(255 CHAR),
      CONSTRAINT "INTERVENTION_PK" PRIMARY KEY ("ID") ENABLE,
      CONSTRAINT "IV_RESOURCE_FK" FOREIGN KEY ("ID") REFERENCES "resource" ("ID") ON DELETE CASCADE ENABLE
 );

COMMIT;
