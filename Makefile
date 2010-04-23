#!/usr/bin/make
#
# Makefile for UTUTI Sandbox
#

BOOTSTRAP_PYTHON=python2.5
TIMEOUT=1
BUILDOUT = bin/buildout -t $(TIMEOUT) && touch bin/*


.PHONY: all
all: python/bin/python bin/buildout bin/paster

python/bin/python:
	$(MAKE) BOOTSTRAP_PYTHON=$(BOOTSTRAP_PYTHON) bootstrap

bin/buildout: bootstrap.py
	$(MAKE) BOOTSTRAP_PYTHON=$(BOOTSTRAP_PYTHON) bootstrap

bin/test: buildout.cfg bin/buildout setup.py versions.cfg
	$(BUILDOUT)

bin/py: buildout.cfg bin/buildout setup.py versions.cfg
	$(BUILDOUT)

bin/paster: buildout.cfg bin/buildout setup.py versions.cfg
	$(BUILDOUT)

bin/tags: buildout.cfg bin/buildout setup.py versions.cfg
	$(BUILDOUT)

export PGPORT ?= 4455
PG_PATH = /usr/lib/postgresql/8.3

instance/var/data/postgresql.conf:
	mkdir -p ${PWD}/instance/var/data
	${PG_PATH}/bin/initdb -D ${PWD}/instance/var/data -E UNICODE

instance/var/data/initialized:
	${PG_PATH}/bin/createuser --createdb    --no-createrole --no-superuser --login admin -h ${PWD}/instance/var/run
	${PG_PATH}/bin/createuser --no-createdb --no-createrole --no-superuser --login test -h ${PWD}/instance/var/run
	${PG_PATH}/bin/createdb --owner test -E UTF8 test -h ${PWD}/instance/var/run
	${PG_PATH}/bin/createlang plpgsql test -h ${PWD}/instance/var/run
	${PG_PATH}/bin/createdb --owner admin -E UTF8 development -h ${PWD}/instance/var/run
	${PG_PATH}/bin/createlang plpgsql development -h ${PWD}/instance/var/run
	bin/paster setup-app development.ini
	echo 1 > ${PWD}/instance/var/data/initialized

instance/done: instance/var/data/postgresql.conf
	$(MAKE) start_database
	$(MAKE) instance/var/data/initialized
	$(MAKE) stop_database
	echo 1 > ${PWD}/instance/done

instance/var/run/.s.PGSQL.${PGPORT}:
	mkdir -p ${PWD}/instance/var/run
	mkdir -p ${PWD}/instance/var/log
	${PG_PATH}/bin/pg_ctl -D ${PWD}/instance/var/data -o "-c unix_socket_directory=${PWD}/instance/var/run/ -c custom_variable_classes='ututi' -c ututi.active_user=0" start  -l ${PWD}/instance/var/log/pg.log
	sleep 5

.PHONY: testpsql
testpsql:
	psql -h ${PWD}/instance/var/run/ -d test

.PHONY: devpsql
devpsql:
	psql -h ${PWD}/instance/var/run/ -d development

reset_devdb: instance/var/run/.s.PGSQL.${PGPORT}
	psql -h ${PWD}/instance/var/run/ -d development -c "drop schema public cascade"
	psql -h ${PWD}/instance/var/run/ -d development -c "create schema public"
	rm -rf ${PWD}/instance/uploads
	bin/paster setup-app development.ini

.PHONY: instance
instance: instance/done

.PHONY: start_database
start_database: instance/var/data/postgresql.conf instance/var/run/.s.PGSQL.${PGPORT}

.PHONY: stop_database
stop_database:
	test -f ${PWD}/instance/var/data/postmaster.pid && ${PG_PATH}/bin/pg_ctl -D ${PWD}/instance/var/data stop -o "-c unix_socket_directory=${PWD}/instance/var/run/" || true

tags: buildout.cfg bin/buildout setup.py bin/tags
	bin/tags

TAGS: buildout.cfg bin/buildout setup.py bin/tags
	bin/tags

ID: buildout.cfg bin/buildout setup.py bin/tags
	bin/tags

.PHONY: bootstrap
bootstrap:
	$(BOOTSTRAP_PYTHON) bootstrap.py

.PHONY: buildout
buildout:
	$(BUILDOUT)

.PHONY: test
test: bin/test instance/done instance/var/run/.s.PGSQL.${PGPORT}
	bin/test --all

.PHONY: utest
testall: bin/test
	bin/test -u

.PHONY: ftest
ftest: bin/test instance/done instance/var/run/.s.PGSQL.${PGPORT}
	bin/test -f --at-level 2

.PHONY: run
run: bin/paster instance/done instance/var/run/.s.PGSQL.${PGPORT}
	bin/paster serve development.ini --reload --monitor-restart

.PHONY: start_testing
start_testing: bin/paster
	bin/paster serve ${PWD}/deployment/testing.ini --daemon --pid-file=${PWD}/deployment/testing.pid --log-file=${PWD}/deployment/testing.log

.PHONY: start_debugging
start_debugging: bin/paster
	bin/paster serve ${PWD}/deployment/debugging.ini --daemon --pid-file=${PWD}/deployment/debugging.pid --log-file=${PWD}/deployment/testing.log

.PHONY: start_staging
start_staging: bin/paster
	bin/paster serve ${PWD}/deployment/staging.ini --daemon --pid-file=${PWD}/deployment/staging.pid --log-file=${PWD}/deployment/testing.log

.PHONY: start_release
start_release: bin/paster
	bin/paster serve ${PWD}/deployment/release.ini --daemon --pid-file=${PWD}/deployment/release.pid --log-file=${PWD}/deployment/testing.log

.PHONY: stop_testing
stop_testing: bin/paster
	bin/paster serve ${PWD}/deployment/testing.ini --stop-daemon --pid-file=${PWD}/deployment/testing.pid

.PHONY: stop_debugging
stop_debugging: bin/paster
	bin/paster serve ${PWD}/deployment/debugging.ini --stop-daemon --pid-file=${PWD}/deployment/debugging.pid

.PHONY: stop_staging
stop_staging: bin/paster
	bin/paster serve ${PWD}/deployment/staging.ini --stop-daemon --pid-file=${PWD}/deployment/staging.pid

.PHONY: stop_release
stop_release: bin/paster
	bin/paster serve ${PWD}/deployment/release.ini --stop-daemon --pid-file=${PWD}/deployment/release.pid

.PHONY: clean
clean:
	rm -rf bin/ parts/ develop-eggs/ src/ututi.egg-info/ python/ tags TAGS ID .installed.cfg

.PHONY: coverage
coverage: bin/test
	rm -rf .coverage
	bin/coverage run bin/test

.PHONY: coverage_report
coverage_report: bin/test .coverage
	rm -rf coverage
	bin/coverage html -d ./coverage/ --omit=/usr,src/ututi/tests,$(HOME)/.buildout,src/ututi/migration

.PHONY: extract-translations
extract-translations: bin/py
	rm -rf src/ututi/templates_py
	cp -r data/templates src/ututi/templates_py
	bin/py setup.py extract_messages --no-location
	rm -rf src/ututi/templates_py
	bin/py setup.py update_catalog --ignore-obsolete=yes --no-fuzzy-matching
	for file in $$(find src/ututi/i18n -name "*.po" -type f); do \
	   sed -e "s/#, fuzzy, python-format/#, python-format/ig" $$file > /tmp/tempfile.tmp; \
	   mv /tmp/tempfile.tmp $$file; \
	   echo "Modified: " $$file; \
	done

.PHONY: compile-translations
compile-translations: bin/py
	bin/py setup.py compile_catalog

.PHONY: ubuntu-environment
ubuntu-environment:
	@if [ `whoami` != "root" ]; then { \
	 echo "You must be root to create an environment."; \
	 echo "I am running as $(shell whoami)"; \
	 exit 3; \
	} else { \
	 apt-get build-dep python-psycopg2 python-imaging python-lxml; \
	 apt-get install build-essential python-all python-all-dev postgresql enscript myspell-lt myspell-en-gb myspell-pl libxslt1-dev libpq-dev; \
	 apt-get remove  python-egenix-mx-base-dev; \
	 echo "Installation Complete: Next... Run 'make'."; \
	} fi

.PHONY: shell
shell: bin/paster instance/done instance/var/run/.s.PGSQL.${PGPORT}
	bin/paster --plugin=Pylons shell development.ini

export BUILD_ID ?= `date +%Y-%m-%d_%H-%M-%S`

.PHONY: package_release
package_release:
	git archive --prefix=ututi${BUILD_ID}/ HEAD | gzip > ututi${BUILD_ID}.tar.gz

.PHONY: download_backup
download_backup:
	scp ututi.lt:/srv/u2ti.com/backup/dbdump ./backup/dbdump

.PHONY: import_backup
import_backup: instance/var/run/.s.PGSQL.${PGPORT}
	psql -h ${PWD}/instance/var/run/ -d development -c "drop schema public cascade"
	psql -h ${PWD}/instance/var/run/ -d development -c "create schema public"
	/usr/lib/postgresql/8.3/bin/pg_restore -d development -h ${PWD}/instance/var/run --no-owner < backup/dbdump || true

.PHONY: download_backup_files
download_backup_files:
	rsync -rtv ututi.lt:/srv/u2ti.com/backup/files_dump/ ./backup/files_dump/

.PHONY: test_migration
test_migration: instance/var/run/.s.PGSQL.${PGPORT}
	psql -h ${PWD}/instance/var/run/ -d development -c "drop schema public cascade"
	psql -h ${PWD}/instance/var/run/ -d development -c "create schema public"
	/usr/lib/postgresql/8.3/bin/pg_restore -d development -h ${PWD}/instance/var/run --no-owner < backup/dbdump || true
	/usr/lib/postgresql/8.3/bin/pg_dump --format=p -h ${PWD}/instance/var/run/ -p 4455 -d development -s > before_migration.txt
	${PWD}/bin/migrate development.ini upgrade_once
	/usr/lib/postgresql/8.3/bin/pg_dump --format=p -h ${PWD}/instance/var/run/ -p 4455 -d development -s > after_migration.txt
	${PWD}/bin/migrate development.ini downgrade
	/usr/lib/postgresql/8.3/bin/pg_dump --format=p -h ${PWD}/instance/var/run/ -p 4455 -d development -s > after_downgrade.txt

.PHONY: test_migration_2
test_migration_2: instance/var/run/.s.PGSQL.${PGPORT}
	psql -h ${PWD}/instance/var/run/ -d development -c "drop schema public cascade"
	psql -h ${PWD}/instance/var/run/ -d development -c "create schema public"
	${PWD}/bin/paster setup-app development.ini
	/usr/lib/postgresql/8.3/bin/pg_dump --format=p -h ${PWD}/instance/var/run/ -p 4455 -d development -s > default.txt
	psql -h ${PWD}/instance/var/run/ -d development -c "drop schema public cascade"
	psql -h ${PWD}/instance/var/run/ -d development -c "create schema public"
	/usr/lib/postgresql/8.3/bin/pg_restore -d development -h ${PWD}/instance/var/run --no-owner < backup/dbdump || true
	${PWD}/bin/migrate development.ini
	/usr/lib/postgresql/8.3/bin/pg_dump --format=p -h ${PWD}/instance/var/run/ -p 4455 -d development -s > actual.txt

.PHONY: test_translations
test_translations: bin/pofilter
	bin/pofilter --progress=none -t xmltags -t printf --ututi ${PWD}/src/ututi/i18n/ -o ${PWD}/parts/test_translations/
	diff -r -u ${PWD}/src/ututi/tests/expected_i18n_errors/lt ${PWD}/parts/test_translations/lt

.coverage: bin/coverage bin/test
	bin/coverage run bin/test

# As our translation extraction depends on coverage, we test coverage
# of templates any non-covered template might not get it's
# translations extracted, which is very risky.
.PHONY: test_template_coverage
test_template_coverage: bin/coverage .coverage
	bin/coverage report --omit=/usr,eggs,src/ututi/tests,$(HOME)/.buildout,src/ututi/migration | grep mako | awk  '{print $$1}' | sed s/data/src\\/ututi/ | sort > parts/test/covered_templates.txt
	find src/ututi -name "*.mako" | sort > parts/test/all_templates.txt
	diff -u parts/test/all_templates.txt parts/test/covered_templates.txt

.PHONY: update_expected_translations
update_expected_translations: bin/pofilter
	bin/pofilter --progress=none -t xmltags -t printf --ututi ${PWD}/src/ututi/i18n/ -o ${PWD}/parts/test_translations/
	rm -rf ${PWD}/src/ututi/tests/expected_i18n_errors/
	mv ${PWD}/parts/test_translations/ ${PWD}/src/ututi/tests/expected_i18n_errors/

.PHONY: test_all
test_all: bin/test bin/coverage instance/done instance/var/run/.s.PGSQL.${PGPORT}
	rm -rf data/templates/
	bin/coverage run bin/test --all
	$(MAKE) test_template_coverage
	$(MAKE) test_translations

