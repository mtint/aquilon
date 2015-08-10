CREATE SEQUENCE network_compartment_id_seq;
CREATE TABLE network_compartment (
	id INTEGER CONSTRAINT "NETWORK_COMPARTMENT_ID_NN" NOT NULL,
	name VARCHAR2(32 CHAR) CONSTRAINT "NETWORK_COMPARTMENT_NAME_NN" NOT NULL,
	creation_date DATE CONSTRAINT "NETWORK_COMPARTMENT_CR_DATE_NN" NOT NULL,
	comments VARCHAR2(255 CHAR),
	CONSTRAINT "NETWORK_COMPARTMENT_PK" PRIMARY KEY (id),
	CONSTRAINT "NETWORK_COMPARTMENT_NAME_UK" UNIQUE (name)
);

QUIT;
