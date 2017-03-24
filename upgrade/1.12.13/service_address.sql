ALTER TABLE service_address DROP CONSTRAINT service_address_dns_record_uk;
DROP INDEX service_address_dns_record_uk;
CREATE INDEX service_address_dns_record_idx ON service_address (dns_record_id);

QUIT;
