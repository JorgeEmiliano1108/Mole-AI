deepmole@mole:~/Escritorio/Mole-AI$ tree
.
├── core_backend
│   ├── apps
│   │   ├── ai_models
│   │   │   ├── admin.py
│   │   │   ├── application
│   │   │   │   └── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── domain
│   │   │   │   └── __init__.py
│   │   │   ├── infrastructure
│   │   │   │   ├── clients
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── repositories
│   │   │   │       └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── migrations
│   │   │   │   ├── 0001_initial.py
│   │   │   │   ├── 0002_alter_cnninference_embedding_vector_and_more.py
│   │   │   │   ├── 0003_alter_cnninference_user_alter_llmrequest_user.py
│   │   │   │   └── __init__.py
│   │   │   ├── models.py
│   │   │   ├── presentation
│   │   │   │   └── __init__.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   ├── tests
│   │   │   │   └── test_vision_status_view.py
│   │   │   ├── urls.py
│   │   │   ├── utils.py
│   │   │   └── views.py
│   │   ├── ai_rag_service
│   │   │   └── __init__.py
│   │   ├── authentication
│   │   │   ├── admin.py
│   │   │   ├── application
│   │   │   │   └── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── domain
│   │   │   │   └── __init__.py
│   │   │   ├── infrastructure
│   │   │   │   ├── authentication.py
│   │   │   │   ├── clients
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── repositories
│   │   │   │       └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── jwks.py
│   │   │   ├── management
│   │   │   │   └── commands
│   │   │   │       ├── backfill_supabase_roles.py
│   │   │   │       └── setup_superuser.py
│   │   │   ├── middleware.py
│   │   │   ├── migrations
│   │   │   │   ├── 0001_initial.py
│   │   │   │   ├── 0002_user_data_consent_user_data_consent_date.py
│   │   │   │   └── __init__.py
│   │   │   ├── models.py
│   │   │   ├── presentation
│   │   │   │   └── __init__.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   ├── core
│   │   │   ├── admin.py
│   │   │   ├── admin_views.py
│   │   │   ├── api_views.py
│   │   │   ├── application
│   │   │   │   └── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── consumers.py
│   │   │   ├── domain
│   │   │   │   ├── entities.py
│   │   │   │   └── __init__.py
│   │   │   ├── infrastructure
│   │   │   │   ├── clients
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── microservices.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── repositories
│   │   │   │       └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── migrations
│   │   │   │   ├── 0001_canonical_initial.py
│   │   │   │   ├── 0002_alter_sensorlog_air_temperature_and_more.py
│   │   │   │   ├── 0003_auto_20260321_2232.py
│   │   │   │   ├── 0004_auditlog.py
│   │   │   │   ├── 0005_aidiagnostic_user.py
│   │   │   │   ├── _archive
│   │   │   │   │   ├── 0001_initial.py
│   │   │   │   │   ├── 0002_alter_sensorlog_sensor_type_and_more.py
│   │   │   │   │   ├── 0003_wide_table_sensor_logs.py
│   │   │   │   │   ├── 0004_diagnosticos_geolocalizados.py
│   │   │   │   │   ├── 0005_botanicalknowledge_feedbackticket_and_more.py
│   │   │   │   │   ├── 0006_sensorlog_hardware_sync.py
│   │   │   │   │   └── 0007_remove_sensorlog_sensor_logs_device__a5cbe0_idx_and_more.py
│   │   │   │   └── __init__.py
│   │   │   ├── models.py
│   │   │   ├── presentation
│   │   │   │   └── __init__.py
│   │   │   ├── routing.py
│   │   │   ├── serializers.py
│   │   │   ├── services
│   │   │   │   ├── __init__.py
│   │   │   │   └── pdf_generator.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   ├── tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_admin_integration.py
│   │   │   │   ├── test_audit.py
│   │   │   │   └── test_chat_history.py
│   │   │   ├── throttles.py
│   │   │   ├── urls.py
│   │   │   ├── urls_root.py
│   │   │   └── views.py
│   │   ├── __init__.py
│   │   └── plants
│   │       ├── apps.py
│   │       ├── infrastructure
│   │       │   ├── __init__.py
│   │       │   └── repositories
│   │       │       └── __init__.py
│   │       ├── __init__.py
│   │       ├── management
│   │       │   ├── commands
│   │       │   │   ├── __init__.py
│   │       │   │   ├── seed_mexican_plants.py
│   │       │   │   └── seed_plants.py
│   │       │   └── __init__.py
│   │       ├── migrations
│   │       │   ├── 0001_initial.py
│   │       │   ├── 0002_speciescatalog_description.py
│   │       │   └── __init__.py
│   │       ├── models.py
│   │       ├── presentation
│   │       │   └── __init__.py
│   │       ├── serializers.py
│   │       ├── tests
│   │       │   └── test_farmer_integration.py
│   │       ├── urls.py
│   │       └── views.py
│   ├── build_django.sh
│   ├── cache
│   ├── celerybeat-schedule
│   ├── db.sqlite3
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── logs
│   │   └── django.log
│   ├── manage.py
│   ├── media
│   │   ├── reports
│   │   └── temp
│   ├── mole_ai_backend
│   │   ├── asgi.py
│   │   ├── celery.py
│   │   ├── __init__.py
│   │   ├── path_config.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── requirements.txt
│   ├── staticfiles
│   │   ├── admin
│   │   │   ├── css
│   │   │   │   ├── autocomplete.4a81fc4242d0.css
│   │   │   │   ├── autocomplete.4a81fc4242d0.css.gz
│   │   │   │   ├── autocomplete.css
│   │   │   │   ├── autocomplete.css.gz
│   │   │   │   ├── base.523eb49842a7.css
│   │   │   │   ├── base.523eb49842a7.css.gz
│   │   │   │   ├── base.css
│   │   │   │   ├── base.css.gz
│   │   │   │   ├── changelists.9237a1ac391b.css
│   │   │   │   ├── changelists.9237a1ac391b.css.gz
│   │   │   │   ├── changelists.css
│   │   │   │   ├── changelists.css.gz
│   │   │   │   ├── dark_mode.css
│   │   │   │   ├── dark_mode.css.gz
│   │   │   │   ├── dark_mode.ef27a31af300.css
│   │   │   │   ├── dark_mode.ef27a31af300.css.gz
│   │   │   │   ├── dashboard.css
│   │   │   │   ├── dashboard.css.gz
│   │   │   │   ├── dashboard.e90f2068217b.css
│   │   │   │   ├── dashboard.e90f2068217b.css.gz
│   │   │   │   ├── forms.c14e1cb06392.css
│   │   │   │   ├── forms.c14e1cb06392.css.gz
│   │   │   │   ├── forms.css
│   │   │   │   ├── forms.css.gz
│   │   │   │   ├── login.586129c60a93.css
│   │   │   │   ├── login.586129c60a93.css.gz
│   │   │   │   ├── login.css
│   │   │   │   ├── login.css.gz
│   │   │   │   ├── nav_sidebar.269a1bd44627.css
│   │   │   │   ├── nav_sidebar.269a1bd44627.css.gz
│   │   │   │   ├── nav_sidebar.css
│   │   │   │   ├── nav_sidebar.css.gz
│   │   │   │   ├── responsive.css
│   │   │   │   ├── responsive.css.gz
│   │   │   │   ├── responsive.f6533dab034d.css
│   │   │   │   ├── responsive.f6533dab034d.css.gz
│   │   │   │   ├── responsive_rtl.7d1130848605.css
│   │   │   │   ├── responsive_rtl.7d1130848605.css.gz
│   │   │   │   ├── responsive_rtl.css
│   │   │   │   ├── responsive_rtl.css.gz
│   │   │   │   ├── rtl.512d4b53fc59.css
│   │   │   │   ├── rtl.512d4b53fc59.css.gz
│   │   │   │   ├── rtl.css
│   │   │   │   ├── rtl.css.gz
│   │   │   │   ├── vendor
│   │   │   │   │   └── select2
│   │   │   │   │       ├── LICENSE-SELECT2.f94142512c91.md
│   │   │   │   │       ├── LICENSE-SELECT2.f94142512c91.md.gz
│   │   │   │   │       ├── LICENSE-SELECT2.md
│   │   │   │   │       ├── LICENSE-SELECT2.md.gz
│   │   │   │   │       ├── select2.a2194c262648.css
│   │   │   │   │       ├── select2.a2194c262648.css.gz
│   │   │   │   │       ├── select2.css
│   │   │   │   │       ├── select2.css.gz
│   │   │   │   │       ├── select2.min.9f54e6414f87.css
│   │   │   │   │       ├── select2.min.9f54e6414f87.css.gz
│   │   │   │   │       ├── select2.min.css
│   │   │   │   │       └── select2.min.css.gz
│   │   │   │   ├── widgets.css
│   │   │   │   ├── widgets.css.gz
│   │   │   │   ├── widgets.ee33ab26c7c2.css
│   │   │   │   └── widgets.ee33ab26c7c2.css.gz
│   │   │   ├── img
│   │   │   │   ├── calendar-icons.39b290681a8b.svg
│   │   │   │   ├── calendar-icons.39b290681a8b.svg.gz
│   │   │   │   ├── calendar-icons.svg
│   │   │   │   ├── calendar-icons.svg.gz
│   │   │   │   ├── gis
│   │   │   │   │   ├── move_vertex_off.7a23bf31ef8a.svg
│   │   │   │   │   ├── move_vertex_off.7a23bf31ef8a.svg.gz
│   │   │   │   │   ├── move_vertex_off.svg
│   │   │   │   │   ├── move_vertex_off.svg.gz
│   │   │   │   │   ├── move_vertex_on.0047eba25b67.svg
│   │   │   │   │   ├── move_vertex_on.0047eba25b67.svg.gz
│   │   │   │   │   ├── move_vertex_on.svg
│   │   │   │   │   └── move_vertex_on.svg.gz
│   │   │   │   ├── icon-addlink.d519b3bab011.svg
│   │   │   │   ├── icon-addlink.d519b3bab011.svg.gz
│   │   │   │   ├── icon-addlink.svg
│   │   │   │   ├── icon-addlink.svg.gz
│   │   │   │   ├── icon-alert.034cc7d8a67f.svg
│   │   │   │   ├── icon-alert.034cc7d8a67f.svg.gz
│   │   │   │   ├── icon-alert.svg
│   │   │   │   ├── icon-alert.svg.gz
│   │   │   │   ├── icon-calendar.ac7aea671bea.svg
│   │   │   │   ├── icon-calendar.ac7aea671bea.svg.gz
│   │   │   │   ├── icon-calendar.svg
│   │   │   │   ├── icon-calendar.svg.gz
│   │   │   │   ├── icon-changelink.18d2fd706348.svg
│   │   │   │   ├── icon-changelink.18d2fd706348.svg.gz
│   │   │   │   ├── icon-changelink.svg
│   │   │   │   ├── icon-changelink.svg.gz
│   │   │   │   ├── icon-clock.e1d4dfac3f2b.svg
│   │   │   │   ├── icon-clock.e1d4dfac3f2b.svg.gz
│   │   │   │   ├── icon-clock.svg
│   │   │   │   ├── icon-clock.svg.gz
│   │   │   │   ├── icon-deletelink.564ef9dc3854.svg
│   │   │   │   ├── icon-deletelink.564ef9dc3854.svg.gz
│   │   │   │   ├── icon-deletelink.svg
│   │   │   │   ├── icon-deletelink.svg.gz
│   │   │   │   ├── icon-no.439e821418cd.svg
│   │   │   │   ├── icon-no.439e821418cd.svg.gz
│   │   │   │   ├── icon-no.svg
│   │   │   │   ├── icon-no.svg.gz
│   │   │   │   ├── icon-unknown.a18cb4398978.svg
│   │   │   │   ├── icon-unknown.a18cb4398978.svg.gz
│   │   │   │   ├── icon-unknown-alt.81536e128bb6.svg
│   │   │   │   ├── icon-unknown-alt.81536e128bb6.svg.gz
│   │   │   │   ├── icon-unknown-alt.svg
│   │   │   │   ├── icon-unknown-alt.svg.gz
│   │   │   │   ├── icon-unknown.svg
│   │   │   │   ├── icon-unknown.svg.gz
│   │   │   │   ├── icon-viewlink.41eb31f7826e.svg
│   │   │   │   ├── icon-viewlink.41eb31f7826e.svg.gz
│   │   │   │   ├── icon-viewlink.svg
│   │   │   │   ├── icon-viewlink.svg.gz
│   │   │   │   ├── icon-yes.d2f9f035226a.svg
│   │   │   │   ├── icon-yes.d2f9f035226a.svg.gz
│   │   │   │   ├── icon-yes.svg
│   │   │   │   ├── icon-yes.svg.gz
│   │   │   │   ├── inline-delete.fec1b761f254.svg
│   │   │   │   ├── inline-delete.fec1b761f254.svg.gz
│   │   │   │   ├── inline-delete.svg
│   │   │   │   ├── inline-delete.svg.gz
│   │   │   │   ├── LICENSE
│   │   │   │   ├── LICENSE.2c54f4e1ca1c
│   │   │   │   ├── LICENSE.2c54f4e1ca1c.gz
│   │   │   │   ├── LICENSE.gz
│   │   │   │   ├── README.a70711a38d87.txt
│   │   │   │   ├── README.a70711a38d87.txt.gz
│   │   │   │   ├── README.txt
│   │   │   │   ├── README.txt.gz
│   │   │   │   ├── search.7cf54ff789c6.svg
│   │   │   │   ├── search.7cf54ff789c6.svg.gz
│   │   │   │   ├── search.svg
│   │   │   │   ├── search.svg.gz
│   │   │   │   ├── selector-icons.b4555096cea2.svg
│   │   │   │   ├── selector-icons.b4555096cea2.svg.gz
│   │   │   │   ├── selector-icons.svg
│   │   │   │   ├── selector-icons.svg.gz
│   │   │   │   ├── sorting-icons.3a097b59f104.svg
│   │   │   │   ├── sorting-icons.3a097b59f104.svg.gz
│   │   │   │   ├── sorting-icons.svg
│   │   │   │   ├── sorting-icons.svg.gz
│   │   │   │   ├── tooltag-add.e59d620a9742.svg
│   │   │   │   ├── tooltag-add.e59d620a9742.svg.gz
│   │   │   │   ├── tooltag-add.svg
│   │   │   │   ├── tooltag-add.svg.gz
│   │   │   │   ├── tooltag-arrowright.bbfb788a849e.svg
│   │   │   │   ├── tooltag-arrowright.bbfb788a849e.svg.gz
│   │   │   │   ├── tooltag-arrowright.svg
│   │   │   │   └── tooltag-arrowright.svg.gz
│   │   │   └── js
│   │   │       ├── actions.eac7e3441574.js
│   │   │       ├── actions.eac7e3441574.js.gz
│   │   │       ├── actions.js
│   │   │       ├── actions.js.gz
│   │   │       ├── admin
│   │   │       │   ├── DateTimeShortcuts.9f6e209cebca.js
│   │   │       │   ├── DateTimeShortcuts.9f6e209cebca.js.gz
│   │   │       │   ├── DateTimeShortcuts.js
│   │   │       │   ├── DateTimeShortcuts.js.gz
│   │   │       │   ├── RelatedObjectLookups.8609f99b9ab2.js
│   │   │       │   ├── RelatedObjectLookups.8609f99b9ab2.js.gz
│   │   │       │   ├── RelatedObjectLookups.js
│   │   │       │   └── RelatedObjectLookups.js.gz
│   │   │       ├── autocomplete.01591ab27be7.js
│   │   │       ├── autocomplete.01591ab27be7.js.gz
│   │   │       ├── autocomplete.js
│   │   │       ├── autocomplete.js.gz
│   │   │       ├── calendar.f8a5d055eb33.js
│   │   │       ├── calendar.f8a5d055eb33.js.gz
│   │   │       ├── calendar.js
│   │   │       ├── calendar.js.gz
│   │   │       ├── cancel.ecc4c5ca7b32.js
│   │   │       ├── cancel.ecc4c5ca7b32.js.gz
│   │   │       ├── cancel.js
│   │   │       ├── cancel.js.gz
│   │   │       ├── change_form.9d8ca4f96b75.js
│   │   │       ├── change_form.9d8ca4f96b75.js.gz
│   │   │       ├── change_form.js
│   │   │       ├── change_form.js.gz
│   │   │       ├── collapse.f84e7410290f.js
│   │   │       ├── collapse.f84e7410290f.js.gz
│   │   │       ├── collapse.js
│   │   │       ├── collapse.js.gz
│   │   │       ├── core.cf103cd04ebf.js
│   │   │       ├── core.cf103cd04ebf.js.gz
│   │   │       ├── core.js
│   │   │       ├── core.js.gz
│   │   │       ├── filters.0e360b7a9f80.js
│   │   │       ├── filters.0e360b7a9f80.js.gz
│   │   │       ├── filters.js
│   │   │       ├── filters.js.gz
│   │   │       ├── inlines.22d4d93c00b4.js
│   │   │       ├── inlines.22d4d93c00b4.js.gz
│   │   │       ├── inlines.js
│   │   │       ├── inlines.js.gz
│   │   │       ├── jquery.init.b7781a0897fc.js
│   │   │       ├── jquery.init.b7781a0897fc.js.gz
│   │   │       ├── jquery.init.js
│   │   │       ├── jquery.init.js.gz
│   │   │       ├── nav_sidebar.3b9190d420b1.js
│   │   │       ├── nav_sidebar.3b9190d420b1.js.gz
│   │   │       ├── nav_sidebar.js
│   │   │       ├── nav_sidebar.js.gz
│   │   │       ├── popup_response.c6cc78ea5551.js
│   │   │       ├── popup_response.c6cc78ea5551.js.gz
│   │   │       ├── popup_response.js
│   │   │       ├── popup_response.js.gz
│   │   │       ├── prepopulate.bd2361dfd64d.js
│   │   │       ├── prepopulate.bd2361dfd64d.js.gz
│   │   │       ├── prepopulate_init.6cac7f3105b8.js
│   │   │       ├── prepopulate_init.6cac7f3105b8.js.gz
│   │   │       ├── prepopulate_init.js
│   │   │       ├── prepopulate_init.js.gz
│   │   │       ├── prepopulate.js
│   │   │       ├── prepopulate.js.gz
│   │   │       ├── SelectBox.7d3ce5a98007.js
│   │   │       ├── SelectBox.7d3ce5a98007.js.gz
│   │   │       ├── SelectBox.js
│   │   │       ├── SelectBox.js.gz
│   │   │       ├── SelectFilter2.bdb8d0cc579e.js
│   │   │       ├── SelectFilter2.bdb8d0cc579e.js.gz
│   │   │       ├── SelectFilter2.js
│   │   │       ├── SelectFilter2.js.gz
│   │   │       ├── theme.ab270f56bb9c.js
│   │   │       ├── theme.ab270f56bb9c.js.gz
│   │   │       ├── theme.js
│   │   │       ├── theme.js.gz
│   │   │       ├── urlify.ae970a820212.js
│   │   │       ├── urlify.ae970a820212.js.gz
│   │   │       ├── urlify.js
│   │   │       ├── urlify.js.gz
│   │   │       └── vendor
│   │   │           ├── jquery
│   │   │           │   ├── jquery.0208b96062ba.js
│   │   │           │   ├── jquery.0208b96062ba.js.gz
│   │   │           │   ├── jquery.js
│   │   │           │   ├── jquery.js.gz
│   │   │           │   ├── jquery.min.641dd1437010.js
│   │   │           │   ├── jquery.min.641dd1437010.js.gz
│   │   │           │   ├── jquery.min.js
│   │   │           │   ├── jquery.min.js.gz
│   │   │           │   ├── LICENSE.de877aa6d744.txt
│   │   │           │   ├── LICENSE.de877aa6d744.txt.gz
│   │   │           │   ├── LICENSE.txt
│   │   │           │   └── LICENSE.txt.gz
│   │   │           ├── select2
│   │   │           │   ├── i18n
│   │   │           │   │   ├── af.4f6fcd73488c.js
│   │   │           │   │   ├── af.4f6fcd73488c.js.gz
│   │   │           │   │   ├── af.js
│   │   │           │   │   ├── af.js.gz
│   │   │           │   │   ├── ar.65aa8e36bf5d.js
│   │   │           │   │   ├── ar.65aa8e36bf5d.js.gz
│   │   │           │   │   ├── ar.js
│   │   │           │   │   ├── ar.js.gz
│   │   │           │   │   ├── az.270c257daf81.js
│   │   │           │   │   ├── az.270c257daf81.js.gz
│   │   │           │   │   ├── az.js
│   │   │           │   │   ├── az.js.gz
│   │   │           │   │   ├── bg.39b8be30d4f0.js
│   │   │           │   │   ├── bg.39b8be30d4f0.js.gz
│   │   │           │   │   ├── bg.js
│   │   │           │   │   ├── bg.js.gz
│   │   │           │   │   ├── bn.6d42b4dd5665.js
│   │   │           │   │   ├── bn.6d42b4dd5665.js.gz
│   │   │           │   │   ├── bn.js
│   │   │           │   │   ├── bn.js.gz
│   │   │           │   │   ├── bs.91624382358e.js
│   │   │           │   │   ├── bs.91624382358e.js.gz
│   │   │           │   │   ├── bs.js
│   │   │           │   │   ├── bs.js.gz
│   │   │           │   │   ├── ca.a166b745933a.js
│   │   │           │   │   ├── ca.a166b745933a.js.gz
│   │   │           │   │   ├── ca.js
│   │   │           │   │   ├── ca.js.gz
│   │   │           │   │   ├── cs.4f43e8e7d33a.js
│   │   │           │   │   ├── cs.4f43e8e7d33a.js.gz
│   │   │           │   │   ├── cs.js
│   │   │           │   │   ├── cs.js.gz
│   │   │           │   │   ├── da.766346afe4dd.js
│   │   │           │   │   ├── da.766346afe4dd.js.gz
│   │   │           │   │   ├── da.js
│   │   │           │   │   ├── da.js.gz
│   │   │           │   │   ├── de.8a1c222b0204.js
│   │   │           │   │   ├── de.8a1c222b0204.js.gz
│   │   │           │   │   ├── de.js
│   │   │           │   │   ├── de.js.gz
│   │   │           │   │   ├── dsb.56372c92d2f1.js
│   │   │           │   │   ├── dsb.56372c92d2f1.js.gz
│   │   │           │   │   ├── dsb.js
│   │   │           │   │   ├── dsb.js.gz
│   │   │           │   │   ├── el.27097f071856.js
│   │   │           │   │   ├── el.27097f071856.js.gz
│   │   │           │   │   ├── el.js
│   │   │           │   │   ├── el.js.gz
│   │   │           │   │   ├── en.cf932ba09a98.js
│   │   │           │   │   ├── en.cf932ba09a98.js.gz
│   │   │           │   │   ├── en.js
│   │   │           │   │   ├── en.js.gz
│   │   │           │   │   ├── es.66dbc2652fb1.js
│   │   │           │   │   ├── es.66dbc2652fb1.js.gz
│   │   │           │   │   ├── es.js
│   │   │           │   │   ├── es.js.gz
│   │   │           │   │   ├── et.2b96fd98289d.js
│   │   │           │   │   ├── et.2b96fd98289d.js.gz
│   │   │           │   │   ├── et.js
│   │   │           │   │   ├── et.js.gz
│   │   │           │   │   ├── eu.adfe5c97b72c.js
│   │   │           │   │   ├── eu.adfe5c97b72c.js.gz
│   │   │           │   │   ├── eu.js
│   │   │           │   │   ├── eu.js.gz
│   │   │           │   │   ├── fa.3b5bd1961cfd.js
│   │   │           │   │   ├── fa.3b5bd1961cfd.js.gz
│   │   │           │   │   ├── fa.js
│   │   │           │   │   ├── fa.js.gz
│   │   │           │   │   ├── fi.614ec42aa9ba.js
│   │   │           │   │   ├── fi.614ec42aa9ba.js.gz
│   │   │           │   │   ├── fi.js
│   │   │           │   │   ├── fi.js.gz
│   │   │           │   │   ├── fr.05e0542fcfe6.js
│   │   │           │   │   ├── fr.05e0542fcfe6.js.gz
│   │   │           │   │   ├── fr.js
│   │   │           │   │   ├── fr.js.gz
│   │   │           │   │   ├── gl.d99b1fedaa86.js
│   │   │           │   │   ├── gl.d99b1fedaa86.js.gz
│   │   │           │   │   ├── gl.js
│   │   │           │   │   ├── gl.js.gz
│   │   │           │   │   ├── he.e420ff6cd3ed.js
│   │   │           │   │   ├── he.e420ff6cd3ed.js.gz
│   │   │           │   │   ├── he.js
│   │   │           │   │   ├── he.js.gz
│   │   │           │   │   ├── hi.70640d41628f.js
│   │   │           │   │   ├── hi.70640d41628f.js.gz
│   │   │           │   │   ├── hi.js
│   │   │           │   │   ├── hi.js.gz
│   │   │           │   │   ├── hr.a2b092cc1147.js
│   │   │           │   │   ├── hr.a2b092cc1147.js.gz
│   │   │           │   │   ├── hr.js
│   │   │           │   │   ├── hr.js.gz
│   │   │           │   │   ├── hsb.fa3b55265efe.js
│   │   │           │   │   ├── hsb.fa3b55265efe.js.gz
│   │   │           │   │   ├── hsb.js
│   │   │           │   │   ├── hsb.js.gz
│   │   │           │   │   ├── hu.6ec6039cb8a3.js
│   │   │           │   │   ├── hu.6ec6039cb8a3.js.gz
│   │   │           │   │   ├── hu.js
│   │   │           │   │   ├── hu.js.gz
│   │   │           │   │   ├── hy.c7babaeef5a6.js
│   │   │           │   │   ├── hy.c7babaeef5a6.js.gz
│   │   │           │   │   ├── hy.js
│   │   │           │   │   ├── hy.js.gz
│   │   │           │   │   ├── id.04debded514d.js
│   │   │           │   │   ├── id.04debded514d.js.gz
│   │   │           │   │   ├── id.js
│   │   │           │   │   ├── id.js.gz
│   │   │           │   │   ├── is.3ddd9a6a97e9.js
│   │   │           │   │   ├── is.3ddd9a6a97e9.js.gz
│   │   │           │   │   ├── is.js
│   │   │           │   │   ├── is.js.gz
│   │   │           │   │   ├── it.be4fe8d365b5.js
│   │   │           │   │   ├── it.be4fe8d365b5.js.gz
│   │   │           │   │   ├── it.js
│   │   │           │   │   ├── it.js.gz
│   │   │           │   │   ├── ja.170ae885d74f.js
│   │   │           │   │   ├── ja.170ae885d74f.js.gz
│   │   │           │   │   ├── ja.js
│   │   │           │   │   ├── ja.js.gz
│   │   │           │   │   ├── ka.2083264a54f0.js
│   │   │           │   │   ├── ka.2083264a54f0.js.gz
│   │   │           │   │   ├── ka.js
│   │   │           │   │   ├── ka.js.gz
│   │   │           │   │   ├── km.c23089cb06ca.js
│   │   │           │   │   ├── km.c23089cb06ca.js.gz
│   │   │           │   │   ├── km.js
│   │   │           │   │   ├── km.js.gz
│   │   │           │   │   ├── ko.e7be6c20e673.js
│   │   │           │   │   ├── ko.e7be6c20e673.js.gz
│   │   │           │   │   ├── ko.js
│   │   │           │   │   ├── ko.js.gz
│   │   │           │   │   ├── lt.23c7ce903300.js
│   │   │           │   │   ├── lt.23c7ce903300.js.gz
│   │   │           │   │   ├── lt.js
│   │   │           │   │   ├── lt.js.gz
│   │   │           │   │   ├── lv.08e62128eac1.js
│   │   │           │   │   ├── lv.08e62128eac1.js.gz
│   │   │           │   │   ├── lv.js
│   │   │           │   │   ├── lv.js.gz
│   │   │           │   │   ├── mk.dabbb9087130.js
│   │   │           │   │   ├── mk.dabbb9087130.js.gz
│   │   │           │   │   ├── mk.js
│   │   │           │   │   ├── mk.js.gz
│   │   │           │   │   ├── ms.4ba82c9a51ce.js
│   │   │           │   │   ├── ms.4ba82c9a51ce.js.gz
│   │   │           │   │   ├── ms.js
│   │   │           │   │   ├── ms.js.gz
│   │   │           │   │   ├── nb.da2fce143f27.js
│   │   │           │   │   ├── nb.da2fce143f27.js.gz
│   │   │           │   │   ├── nb.js
│   │   │           │   │   ├── nb.js.gz
│   │   │           │   │   ├── ne.3d79fd3f08db.js
│   │   │           │   │   ├── ne.3d79fd3f08db.js.gz
│   │   │           │   │   ├── ne.js
│   │   │           │   │   ├── ne.js.gz
│   │   │           │   │   ├── nl.997868a37ed8.js
│   │   │           │   │   ├── nl.997868a37ed8.js.gz
│   │   │           │   │   ├── nl.js
│   │   │           │   │   ├── nl.js.gz
│   │   │           │   │   ├── pl.6031b4f16452.js
│   │   │           │   │   ├── pl.6031b4f16452.js.gz
│   │   │           │   │   ├── pl.js
│   │   │           │   │   ├── pl.js.gz
│   │   │           │   │   ├── ps.38dfa47af9e0.js
│   │   │           │   │   ├── ps.38dfa47af9e0.js.gz
│   │   │           │   │   ├── ps.js
│   │   │           │   │   ├── ps.js.gz
│   │   │           │   │   ├── pt.33b4a3b44d43.js
│   │   │           │   │   ├── pt.33b4a3b44d43.js.gz
│   │   │           │   │   ├── pt-BR.e1b294433e7f.js
│   │   │           │   │   ├── pt-BR.e1b294433e7f.js.gz
│   │   │           │   │   ├── pt-BR.js
│   │   │           │   │   ├── pt-BR.js.gz
│   │   │           │   │   ├── pt.js
│   │   │           │   │   ├── pt.js.gz
│   │   │           │   │   ├── ro.f75cb460ec3b.js
│   │   │           │   │   ├── ro.f75cb460ec3b.js.gz
│   │   │           │   │   ├── ro.js
│   │   │           │   │   ├── ro.js.gz
│   │   │           │   │   ├── ru.934aa95f5b5f.js
│   │   │           │   │   ├── ru.934aa95f5b5f.js.gz
│   │   │           │   │   ├── ru.js
│   │   │           │   │   ├── ru.js.gz
│   │   │           │   │   ├── sk.33d02cef8d11.js
│   │   │           │   │   ├── sk.33d02cef8d11.js.gz
│   │   │           │   │   ├── sk.js
│   │   │           │   │   ├── sk.js.gz
│   │   │           │   │   ├── sl.131a78bc0752.js
│   │   │           │   │   ├── sl.131a78bc0752.js.gz
│   │   │           │   │   ├── sl.js
│   │   │           │   │   ├── sl.js.gz
│   │   │           │   │   ├── sq.5636b60d29c9.js
│   │   │           │   │   ├── sq.5636b60d29c9.js.gz
│   │   │           │   │   ├── sq.js
│   │   │           │   │   ├── sq.js.gz
│   │   │           │   │   ├── sr.5ed85a48f483.js
│   │   │           │   │   ├── sr.5ed85a48f483.js.gz
│   │   │           │   │   ├── sr-Cyrl.f254bb8c4c7c.js
│   │   │           │   │   ├── sr-Cyrl.f254bb8c4c7c.js.gz
│   │   │           │   │   ├── sr-Cyrl.js
│   │   │           │   │   ├── sr-Cyrl.js.gz
│   │   │           │   │   ├── sr.js
│   │   │           │   │   ├── sr.js.gz
│   │   │           │   │   ├── sv.7a9c2f71e777.js
│   │   │           │   │   ├── sv.7a9c2f71e777.js.gz
│   │   │           │   │   ├── sv.js
│   │   │           │   │   ├── sv.js.gz
│   │   │           │   │   ├── th.f38c20b0221b.js
│   │   │           │   │   ├── th.f38c20b0221b.js.gz
│   │   │           │   │   ├── th.js
│   │   │           │   │   ├── th.js.gz
│   │   │           │   │   ├── tk.7c572a68c78f.js
│   │   │           │   │   ├── tk.7c572a68c78f.js.gz
│   │   │           │   │   ├── tk.js
│   │   │           │   │   ├── tk.js.gz
│   │   │           │   │   ├── tr.b5a0643d1545.js
│   │   │           │   │   ├── tr.b5a0643d1545.js.gz
│   │   │           │   │   ├── tr.js
│   │   │           │   │   ├── tr.js.gz
│   │   │           │   │   ├── uk.8cede7f4803c.js
│   │   │           │   │   ├── uk.8cede7f4803c.js.gz
│   │   │           │   │   ├── uk.js
│   │   │           │   │   ├── uk.js.gz
│   │   │           │   │   ├── vi.097a5b75b3e1.js
│   │   │           │   │   ├── vi.097a5b75b3e1.js.gz
│   │   │           │   │   ├── vi.js
│   │   │           │   │   ├── vi.js.gz
│   │   │           │   │   ├── zh-CN.2cff662ec5f9.js
│   │   │           │   │   ├── zh-CN.2cff662ec5f9.js.gz
│   │   │           │   │   ├── zh-CN.js
│   │   │           │   │   ├── zh-CN.js.gz
│   │   │           │   │   ├── zh-TW.04554a227c2b.js
│   │   │           │   │   ├── zh-TW.04554a227c2b.js.gz
│   │   │           │   │   ├── zh-TW.js
│   │   │           │   │   └── zh-TW.js.gz
│   │   │           │   ├── LICENSE.f94142512c91.md
│   │   │           │   ├── LICENSE.f94142512c91.md.gz
│   │   │           │   ├── LICENSE.md
│   │   │           │   ├── LICENSE.md.gz
│   │   │           │   ├── select2.full.c2afdeda3058.js
│   │   │           │   ├── select2.full.c2afdeda3058.js.gz
│   │   │           │   ├── select2.full.js
│   │   │           │   ├── select2.full.js.gz
│   │   │           │   ├── select2.full.min.fcd7500d8e13.js
│   │   │           │   ├── select2.full.min.fcd7500d8e13.js.gz
│   │   │           │   ├── select2.full.min.js
│   │   │           │   └── select2.full.min.js.gz
│   │   │           └── xregexp
│   │   │               ├── LICENSE.bf79e414957a.txt
│   │   │               ├── LICENSE.bf79e414957a.txt.gz
│   │   │               ├── LICENSE.txt
│   │   │               ├── LICENSE.txt.gz
│   │   │               ├── xregexp.efda034b9537.js
│   │   │               ├── xregexp.efda034b9537.js.gz
│   │   │               ├── xregexp.js
│   │   │               ├── xregexp.js.gz
│   │   │               ├── xregexp.min.b0439563a5d3.js
│   │   │               ├── xregexp.min.b0439563a5d3.js.gz
│   │   │               ├── xregexp.min.js
│   │   │               └── xregexp.min.js.gz
│   │   ├── rest_framework
│   │   │   ├── css
│   │   │   │   ├── bootstrap.min.css
│   │   │   │   ├── bootstrap.min.css.cafbda9c0e9e.map
│   │   │   │   ├── bootstrap.min.css.cafbda9c0e9e.map.gz
│   │   │   │   ├── bootstrap.min.css.gz
│   │   │   │   ├── bootstrap.min.css.map
│   │   │   │   ├── bootstrap.min.css.map.gz
│   │   │   │   ├── bootstrap.min.f17d4516b026.css
│   │   │   │   ├── bootstrap.min.f17d4516b026.css.gz
│   │   │   │   ├── bootstrap-theme.min.1d4b05b397c3.css
│   │   │   │   ├── bootstrap-theme.min.1d4b05b397c3.css.gz
│   │   │   │   ├── bootstrap-theme.min.css
│   │   │   │   ├── bootstrap-theme.min.css.51806092cc05.map
│   │   │   │   ├── bootstrap-theme.min.css.51806092cc05.map.gz
│   │   │   │   ├── bootstrap-theme.min.css.gz
│   │   │   │   ├── bootstrap-theme.min.css.map
│   │   │   │   ├── bootstrap-theme.min.css.map.gz
│   │   │   │   ├── bootstrap-tweaks.css
│   │   │   │   ├── bootstrap-tweaks.css.gz
│   │   │   │   ├── bootstrap-tweaks.ee4ee6acf9eb.css
│   │   │   │   ├── bootstrap-tweaks.ee4ee6acf9eb.css.gz
│   │   │   │   ├── default.789dfb5732d7.css
│   │   │   │   ├── default.789dfb5732d7.css.gz
│   │   │   │   ├── default.css
│   │   │   │   ├── default.css.gz
│   │   │   │   ├── font-awesome-4.0.3.c1e1ea213abf.css
│   │   │   │   ├── font-awesome-4.0.3.c1e1ea213abf.css.gz
│   │   │   │   ├── font-awesome-4.0.3.css
│   │   │   │   ├── font-awesome-4.0.3.css.gz
│   │   │   │   ├── prettify.a987f72342ee.css
│   │   │   │   ├── prettify.a987f72342ee.css.gz
│   │   │   │   ├── prettify.css
│   │   │   │   └── prettify.css.gz
│   │   │   ├── fonts
│   │   │   │   ├── fontawesome-webfont.3293616ec0c6.woff
│   │   │   │   ├── fontawesome-webfont.83e37a11f9d7.svg
│   │   │   │   ├── fontawesome-webfont.83e37a11f9d7.svg.gz
│   │   │   │   ├── fontawesome-webfont.8b27bc96115c.eot
│   │   │   │   ├── fontawesome-webfont.dcb26c7239d8.ttf
│   │   │   │   ├── fontawesome-webfont.dcb26c7239d8.ttf.gz
│   │   │   │   ├── fontawesome-webfont.eot
│   │   │   │   ├── fontawesome-webfont.svg
│   │   │   │   ├── fontawesome-webfont.svg.gz
│   │   │   │   ├── fontawesome-webfont.ttf
│   │   │   │   ├── fontawesome-webfont.ttf.gz
│   │   │   │   ├── fontawesome-webfont.woff
│   │   │   │   ├── glyphicons-halflings-regular.08eda92397ae.svg
│   │   │   │   ├── glyphicons-halflings-regular.08eda92397ae.svg.gz
│   │   │   │   ├── glyphicons-halflings-regular.448c34a56d69.woff2
│   │   │   │   ├── glyphicons-halflings-regular.e18bbf611f2a.ttf
│   │   │   │   ├── glyphicons-halflings-regular.e18bbf611f2a.ttf.gz
│   │   │   │   ├── glyphicons-halflings-regular.eot
│   │   │   │   ├── glyphicons-halflings-regular.f4769f9bdb74.eot
│   │   │   │   ├── glyphicons-halflings-regular.fa2772327f55.woff
│   │   │   │   ├── glyphicons-halflings-regular.svg
│   │   │   │   ├── glyphicons-halflings-regular.svg.gz
│   │   │   │   ├── glyphicons-halflings-regular.ttf
│   │   │   │   ├── glyphicons-halflings-regular.ttf.gz
│   │   │   │   ├── glyphicons-halflings-regular.woff
│   │   │   │   └── glyphicons-halflings-regular.woff2
│   │   │   ├── img
│   │   │   │   ├── glyphicons-halflings.90233c9067e9.png
│   │   │   │   ├── glyphicons-halflings.png
│   │   │   │   ├── glyphicons-halflings-white.9bbc6e960299.png
│   │   │   │   ├── glyphicons-halflings-white.png
│   │   │   │   ├── grid.a4b938cf382b.png
│   │   │   │   └── grid.png
│   │   │   └── js
│   │   │       ├── ajax-form.4e1cdcb7acab.js
│   │   │       ├── ajax-form.4e1cdcb7acab.js.gz
│   │   │       ├── ajax-form.js
│   │   │       ├── ajax-form.js.gz
│   │   │       ├── bootstrap.min.2f34b630ffe3.js
│   │   │       ├── bootstrap.min.2f34b630ffe3.js.gz
│   │   │       ├── bootstrap.min.js
│   │   │       ├── bootstrap.min.js.gz
│   │   │       ├── csrf.455080a7b2ce.js
│   │   │       ├── csrf.455080a7b2ce.js.gz
│   │   │       ├── csrf.js
│   │   │       ├── csrf.js.gz
│   │   │       ├── default.5b08897dbdc3.js
│   │   │       ├── default.5b08897dbdc3.js.gz
│   │   │       ├── default.js
│   │   │       ├── default.js.gz
│   │   │       ├── jquery-3.7.1.min.2c872dbe60f4.js
│   │   │       ├── jquery-3.7.1.min.2c872dbe60f4.js.gz
│   │   │       ├── jquery-3.7.1.min.js
│   │   │       ├── jquery-3.7.1.min.js.gz
│   │   │       ├── load-ajax-form.8cdb3a9f3466.js
│   │   │       ├── load-ajax-form.js
│   │   │       ├── prettify-min.709bfcc456c6.js
│   │   │       ├── prettify-min.709bfcc456c6.js.gz
│   │   │       ├── prettify-min.js
│   │   │       └── prettify-min.js.gz
│   │   └── staticfiles.json
│   └── tests
│       ├── api_pentest.py
│       ├── __init__.py
│       ├── integration
│       │   ├── __init__.py
│       │   ├── test_feedback_endpoint.py
│       │   ├── test_m2m_ingest_wide_table.py
│       │   └── test_map_hotspots.py
│       ├── resilience_test.py
│       ├── smoke_runner.py
│       ├── test_ai_models
│       │   ├── __init__.py
│       │   ├── test_models.py
│       │   └── test_sensor_data_aggregator.py
│       ├── test_authentication
│       │   ├── __init__.py
│       │   └── test_models.py
│       ├── test_core
│       │   ├── __init__.py
│       │   └── test_models.py
│       ├── test_core_views
│       │   ├── __init__.py
│       │   └── test_sensor_data_patch.py
│       ├── test_singleton_vision_client.py
│       └── test_vision.py
├── docs
│   └── architecture
├── edge_node
│   ├── inference.py
│   ├── __init__.py
│   ├── mqtt_local_subscriber.py
│   ├── requirements.txt
│   └── store_forward_daemon.py
├── esp32_wide_table_snippet.cpp
├── frontend
│   ├── admin.html
│   ├── dashboard.html
│   ├── dist
│   │   ├── admin.html
│   │   ├── assets
│   │   │   ├── main-DjWheDDD.css
│   │   │   ├── main-DsXFJaDf.js
│   │   │   ├── planta.jpeg
│   │   │   └── topo.png
│   │   ├── css
│   │   │   └── styles.css
│   │   ├── dashboard.html
│   │   ├── img
│   │   │   ├── bugambilia.jpg
│   │   │   ├── cempasuchil.jpg
│   │   │   ├── hongos.jpg
│   │   │   ├── lavanda.jpg
│   │   │   ├── menta.jpg
│   │   │   ├── peyote.jpg
│   │   │   ├── sabila.jpg
│   │   │   └── toronjil.jpg
│   │   ├── index.html
│   │   ├── js
│   │   │   └── tailwind-compiler.js
│   │   ├── lang
│   │   │   └── es.json
│   │   ├── login.html
│   │   └── vendor
│   │       ├── chart.min.js
│   │       └── leaflet
│   │           ├── images
│   │           │   ├── layers-2x.png
│   │           │   ├── layers.png
│   │           │   ├── marker-icon-2x.png
│   │           │   ├── marker-icon.png
│   │           │   └── marker-shadow.png
│   │           ├── leaflet.css
│   │           └── leaflet.js
│   ├── index.html
│   ├── login.html
│   ├── node_modules
│   │   ├── @alloc
│   │   │   └── quick-lru
│   │   │       ├── index.d.ts
│   │   │       ├── index.js
│   │   │       ├── license
│   │   │       ├── package.json
│   │   │       └── readme.md
│   │   ├── anymatch
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── any-promise
│   │   │   ├── implementation.d.ts
│   │   │   ├── implementation.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── loader.js
│   │   │   ├── optional.js
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── register
│   │   │   │   ├── bluebird.d.ts
│   │   │   │   ├── bluebird.js
│   │   │   │   ├── es6-promise.d.ts
│   │   │   │   ├── es6-promise.js
│   │   │   │   ├── lie.d.ts
│   │   │   │   ├── lie.js
│   │   │   │   ├── native-promise-only.d.ts
│   │   │   │   ├── native-promise-only.js
│   │   │   │   ├── pinkie.d.ts
│   │   │   │   ├── pinkie.js
│   │   │   │   ├── promise.d.ts
│   │   │   │   ├── promise.js
│   │   │   │   ├── q.d.ts
│   │   │   │   ├── q.js
│   │   │   │   ├── rsvp.d.ts
│   │   │   │   ├── rsvp.js
│   │   │   │   ├── vow.d.ts
│   │   │   │   ├── vow.js
│   │   │   │   ├── when.d.ts
│   │   │   │   └── when.js
│   │   │   ├── register.d.ts
│   │   │   ├── register.js
│   │   │   └── register-shim.js
│   │   ├── arg
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE.md
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── autoprefixer
│   │   │   ├── bin
│   │   │   │   └── autoprefixer
│   │   │   ├── data
│   │   │   │   └── prefixes.js
│   │   │   ├── lib
│   │   │   │   ├── at-rule.js
│   │   │   │   ├── autoprefixer.d.ts
│   │   │   │   ├── autoprefixer.js
│   │   │   │   ├── brackets.js
│   │   │   │   ├── browsers.js
│   │   │   │   ├── declaration.js
│   │   │   │   ├── hacks
│   │   │   │   │   ├── align-content.js
│   │   │   │   │   ├── align-items.js
│   │   │   │   │   ├── align-self.js
│   │   │   │   │   ├── animation.js
│   │   │   │   │   ├── appearance.js
│   │   │   │   │   ├── autofill.js
│   │   │   │   │   ├── backdrop-filter.js
│   │   │   │   │   ├── background-clip.js
│   │   │   │   │   ├── background-size.js
│   │   │   │   │   ├── block-logical.js
│   │   │   │   │   ├── border-image.js
│   │   │   │   │   ├── border-radius.js
│   │   │   │   │   ├── break-props.js
│   │   │   │   │   ├── cross-fade.js
│   │   │   │   │   ├── display-flex.js
│   │   │   │   │   ├── display-grid.js
│   │   │   │   │   ├── file-selector-button.js
│   │   │   │   │   ├── filter.js
│   │   │   │   │   ├── filter-value.js
│   │   │   │   │   ├── flex-basis.js
│   │   │   │   │   ├── flex-direction.js
│   │   │   │   │   ├── flex-flow.js
│   │   │   │   │   ├── flex-grow.js
│   │   │   │   │   ├── flex.js
│   │   │   │   │   ├── flex-shrink.js
│   │   │   │   │   ├── flex-spec.js
│   │   │   │   │   ├── flex-wrap.js
│   │   │   │   │   ├── fullscreen.js
│   │   │   │   │   ├── gradient.js
│   │   │   │   │   ├── grid-area.js
│   │   │   │   │   ├── grid-column-align.js
│   │   │   │   │   ├── grid-end.js
│   │   │   │   │   ├── grid-row-align.js
│   │   │   │   │   ├── grid-row-column.js
│   │   │   │   │   ├── grid-rows-columns.js
│   │   │   │   │   ├── grid-start.js
│   │   │   │   │   ├── grid-template-areas.js
│   │   │   │   │   ├── grid-template.js
│   │   │   │   │   ├── grid-utils.js
│   │   │   │   │   ├── image-rendering.js
│   │   │   │   │   ├── image-set.js
│   │   │   │   │   ├── inline-logical.js
│   │   │   │   │   ├── intrinsic.js
│   │   │   │   │   ├── justify-content.js
│   │   │   │   │   ├── mask-border.js
│   │   │   │   │   ├── mask-composite.js
│   │   │   │   │   ├── order.js
│   │   │   │   │   ├── overscroll-behavior.js
│   │   │   │   │   ├── pixelated.js
│   │   │   │   │   ├── placeholder.js
│   │   │   │   │   ├── placeholder-shown.js
│   │   │   │   │   ├── place-self.js
│   │   │   │   │   ├── print-color-adjust.js
│   │   │   │   │   ├── text-decoration.js
│   │   │   │   │   ├── text-decoration-skip-ink.js
│   │   │   │   │   ├── text-emphasis-position.js
│   │   │   │   │   ├── transform-decl.js
│   │   │   │   │   ├── user-select.js
│   │   │   │   │   └── writing-mode.js
│   │   │   │   ├── info.js
│   │   │   │   ├── old-selector.js
│   │   │   │   ├── old-value.js
│   │   │   │   ├── prefixer.js
│   │   │   │   ├── prefixes.js
│   │   │   │   ├── processor.js
│   │   │   │   ├── resolution.js
│   │   │   │   ├── selector.js
│   │   │   │   ├── supports.js
│   │   │   │   ├── transition.js
│   │   │   │   ├── utils.js
│   │   │   │   ├── value.js
│   │   │   │   └── vendor.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── baseline-browser-mapping
│   │   │   ├── dist
│   │   │   │   ├── cli.cjs
│   │   │   │   ├── index.cjs
│   │   │   │   ├── index.d.ts
│   │   │   │   └── index.js
│   │   │   ├── LICENSE.txt
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── binary-extensions
│   │   │   ├── binary-extensions.json
│   │   │   ├── binary-extensions.json.d.ts
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   └── readme.md
│   │   ├── braces
│   │   │   ├── index.js
│   │   │   ├── lib
│   │   │   │   ├── compile.js
│   │   │   │   ├── constants.js
│   │   │   │   ├── expand.js
│   │   │   │   ├── parse.js
│   │   │   │   ├── stringify.js
│   │   │   │   └── utils.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── browserslist
│   │   │   ├── browser.js
│   │   │   ├── cli.js
│   │   │   ├── error.d.ts
│   │   │   ├── error.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── node.js
│   │   │   ├── package.json
│   │   │   ├── parse.js
│   │   │   └── README.md
│   │   ├── camelcase-css
│   │   │   ├── index-es5.js
│   │   │   ├── index.js
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── caniuse-lite
│   │   │   ├── data
│   │   │   │   ├── agents.js
│   │   │   │   ├── browsers.js
│   │   │   │   ├── browserVersions.js
│   │   │   │   ├── features
│   │   │   │   │   ├── aac.js
│   │   │   │   │   ├── abortcontroller.js
│   │   │   │   │   ├── ac3-ec3.js
│   │   │   │   │   ├── accelerometer.js
│   │   │   │   │   ├── addeventlistener.js
│   │   │   │   │   ├── alternate-stylesheet.js
│   │   │   │   │   ├── ambient-light.js
│   │   │   │   │   ├── apng.js
│   │   │   │   │   ├── array-find-index.js
│   │   │   │   │   ├── array-find.js
│   │   │   │   │   ├── array-flat.js
│   │   │   │   │   ├── array-includes.js
│   │   │   │   │   ├── arrow-functions.js
│   │   │   │   │   ├── asmjs.js
│   │   │   │   │   ├── async-clipboard.js
│   │   │   │   │   ├── async-functions.js
│   │   │   │   │   ├── atob-btoa.js
│   │   │   │   │   ├── audio-api.js
│   │   │   │   │   ├── audio.js
│   │   │   │   │   ├── audiotracks.js
│   │   │   │   │   ├── autofocus.js
│   │   │   │   │   ├── auxclick.js
│   │   │   │   │   ├── av1.js
│   │   │   │   │   ├── avif.js
│   │   │   │   │   ├── background-attachment.js
│   │   │   │   │   ├── background-clip-text.js
│   │   │   │   │   ├── background-img-opts.js
│   │   │   │   │   ├── background-position-x-y.js
│   │   │   │   │   ├── background-repeat-round-space.js
│   │   │   │   │   ├── background-sync.js
│   │   │   │   │   ├── battery-status.js
│   │   │   │   │   ├── beacon.js
│   │   │   │   │   ├── beforeafterprint.js
│   │   │   │   │   ├── bigint.js
│   │   │   │   │   ├── blobbuilder.js
│   │   │   │   │   ├── bloburls.js
│   │   │   │   │   ├── border-image.js
│   │   │   │   │   ├── border-radius.js
│   │   │   │   │   ├── broadcastchannel.js
│   │   │   │   │   ├── brotli.js
│   │   │   │   │   ├── calc.js
│   │   │   │   │   ├── canvas-blending.js
│   │   │   │   │   ├── canvas.js
│   │   │   │   │   ├── canvas-text.js
│   │   │   │   │   ├── chacha20-poly1305.js
│   │   │   │   │   ├── channel-messaging.js
│   │   │   │   │   ├── childnode-remove.js
│   │   │   │   │   ├── ch-unit.js
│   │   │   │   │   ├── classlist.js
│   │   │   │   │   ├── client-hints-dpr-width-viewport.js
│   │   │   │   │   ├── clipboard.js
│   │   │   │   │   ├── colr.js
│   │   │   │   │   ├── colr-v1.js
│   │   │   │   │   ├── comparedocumentposition.js
│   │   │   │   │   ├── console-basic.js
│   │   │   │   │   ├── console-time.js
│   │   │   │   │   ├── const.js
│   │   │   │   │   ├── constraint-validation.js
│   │   │   │   │   ├── contenteditable.js
│   │   │   │   │   ├── contentsecuritypolicy2.js
│   │   │   │   │   ├── contentsecuritypolicy.js
│   │   │   │   │   ├── cookie-store-api.js
│   │   │   │   │   ├── cors.js
│   │   │   │   │   ├── createimagebitmap.js
│   │   │   │   │   ├── credential-management.js
│   │   │   │   │   ├── cross-document-view-transitions.js
│   │   │   │   │   ├── cryptography.js
│   │   │   │   │   ├── css3-attr.js
│   │   │   │   │   ├── css3-boxsizing.js
│   │   │   │   │   ├── css3-colors.js
│   │   │   │   │   ├── css3-cursors-grab.js
│   │   │   │   │   ├── css3-cursors.js
│   │   │   │   │   ├── css3-cursors-newer.js
│   │   │   │   │   ├── css3-tabsize.js
│   │   │   │   │   ├── css-all.js
│   │   │   │   │   ├── css-anchor-positioning.js
│   │   │   │   │   ├── css-animation.js
│   │   │   │   │   ├── css-any-link.js
│   │   │   │   │   ├── css-appearance.js
│   │   │   │   │   ├── css-at-counter-style.js
│   │   │   │   │   ├── css-autofill.js
│   │   │   │   │   ├── css-backdrop-filter.js
│   │   │   │   │   ├── css-backgroundblendmode.js
│   │   │   │   │   ├── css-background-offsets.js
│   │   │   │   │   ├── css-boxdecorationbreak.js
│   │   │   │   │   ├── css-boxshadow.js
│   │   │   │   │   ├── css-canvas.js
│   │   │   │   │   ├── css-caret-color.js
│   │   │   │   │   ├── css-cascade-layers.js
│   │   │   │   │   ├── css-cascade-scope.js
│   │   │   │   │   ├── css-case-insensitive.js
│   │   │   │   │   ├── css-clip-path.js
│   │   │   │   │   ├── css-color-adjust.js
│   │   │   │   │   ├── css-color-function.js
│   │   │   │   │   ├── css-conic-gradients.js
│   │   │   │   │   ├── css-container-queries.js
│   │   │   │   │   ├── css-container-queries-style.js
│   │   │   │   │   ├── css-container-query-units.js
│   │   │   │   │   ├── css-containment.js
│   │   │   │   │   ├── css-content-visibility.js
│   │   │   │   │   ├── css-counters.js
│   │   │   │   │   ├── css-crisp-edges.js
│   │   │   │   │   ├── css-cross-fade.js
│   │   │   │   │   ├── css-default-pseudo.js
│   │   │   │   │   ├── css-descendant-gtgt.js
│   │   │   │   │   ├── css-deviceadaptation.js
│   │   │   │   │   ├── css-dir-pseudo.js
│   │   │   │   │   ├── css-display-contents.js
│   │   │   │   │   ├── css-element-function.js
│   │   │   │   │   ├── css-env-function.js
│   │   │   │   │   ├── css-exclusions.js
│   │   │   │   │   ├── css-featurequeries.js
│   │   │   │   │   ├── css-file-selector-button.js
│   │   │   │   │   ├── css-filter-function.js
│   │   │   │   │   ├── css-filters.js
│   │   │   │   │   ├── css-first-letter.js
│   │   │   │   │   ├── css-first-line.js
│   │   │   │   │   ├── css-fixed.js
│   │   │   │   │   ├── css-focus-visible.js
│   │   │   │   │   ├── css-focus-within.js
│   │   │   │   │   ├── css-font-palette.js
│   │   │   │   │   ├── css-font-rendering-controls.js
│   │   │   │   │   ├── css-font-stretch.js
│   │   │   │   │   ├── css-gencontent.js
│   │   │   │   │   ├── css-gradients.js
│   │   │   │   │   ├── css-grid-animation.js
│   │   │   │   │   ├── css-grid.js
│   │   │   │   │   ├── css-grid-lanes.js
│   │   │   │   │   ├── css-hanging-punctuation.js
│   │   │   │   │   ├── css-has.js
│   │   │   │   │   ├── css-hyphens.js
│   │   │   │   │   ├── css-if.js
│   │   │   │   │   ├── css-image-orientation.js
│   │   │   │   │   ├── css-image-set.js
│   │   │   │   │   ├── css-indeterminate-pseudo.js
│   │   │   │   │   ├── css-initial-letter.js
│   │   │   │   │   ├── css-initial-value.js
│   │   │   │   │   ├── css-in-out-of-range.js
│   │   │   │   │   ├── css-lch-lab.js
│   │   │   │   │   ├── css-letter-spacing.js
│   │   │   │   │   ├── css-line-clamp.js
│   │   │   │   │   ├── css-logical-props.js
│   │   │   │   │   ├── css-marker-pseudo.js
│   │   │   │   │   ├── css-masks.js
│   │   │   │   │   ├── css-matches-pseudo.js
│   │   │   │   │   ├── css-math-functions.js
│   │   │   │   │   ├── css-media-interaction.js
│   │   │   │   │   ├── css-mediaqueries.js
│   │   │   │   │   ├── css-media-range-syntax.js
│   │   │   │   │   ├── css-media-resolution.js
│   │   │   │   │   ├── css-media-scripting.js
│   │   │   │   │   ├── css-mixblendmode.js
│   │   │   │   │   ├── css-module-scripts.js
│   │   │   │   │   ├── css-motion-paths.js
│   │   │   │   │   ├── css-namespaces.js
│   │   │   │   │   ├── css-nesting.js
│   │   │   │   │   ├── css-not-sel-list.js
│   │   │   │   │   ├── css-nth-child-of.js
│   │   │   │   │   ├── css-opacity.js
│   │   │   │   │   ├── css-optional-pseudo.js
│   │   │   │   │   ├── css-overflow-anchor.js
│   │   │   │   │   ├── css-overflow.js
│   │   │   │   │   ├── css-overflow-overlay.js
│   │   │   │   │   ├── css-overscroll-behavior.js
│   │   │   │   │   ├── css-page-break.js
│   │   │   │   │   ├── css-paged-media.js
│   │   │   │   │   ├── css-paint-api.js
│   │   │   │   │   ├── css-placeholder.js
│   │   │   │   │   ├── css-placeholder-shown.js
│   │   │   │   │   ├── css-print-color-adjust.js
│   │   │   │   │   ├── css-read-only-write.js
│   │   │   │   │   ├── css-rebeccapurple.js
│   │   │   │   │   ├── css-reflections.js
│   │   │   │   │   ├── css-regions.js
│   │   │   │   │   ├── css-relative-colors.js
│   │   │   │   │   ├── css-repeating-gradients.js
│   │   │   │   │   ├── css-resize.js
│   │   │   │   │   ├── css-revert-value.js
│   │   │   │   │   ├── css-rrggbbaa.js
│   │   │   │   │   ├── css-scrollbar.js
│   │   │   │   │   ├── css-scroll-behavior.js
│   │   │   │   │   ├── css-sel2.js
│   │   │   │   │   ├── css-sel3.js
│   │   │   │   │   ├── css-selection.js
│   │   │   │   │   ├── css-shapes.js
│   │   │   │   │   ├── css-snappoints.js
│   │   │   │   │   ├── css-sticky.js
│   │   │   │   │   ├── css-subgrid.js
│   │   │   │   │   ├── css-supports-api.js
│   │   │   │   │   ├── css-table.js
│   │   │   │   │   ├── css-text-align-last.js
│   │   │   │   │   ├── css-text-box-trim.js
│   │   │   │   │   ├── css-text-indent.js
│   │   │   │   │   ├── css-text-justify.js
│   │   │   │   │   ├── css-text-orientation.js
│   │   │   │   │   ├── css-textshadow.js
│   │   │   │   │   ├── css-text-spacing.js
│   │   │   │   │   ├── css-text-wrap-balance.js
│   │   │   │   │   ├── css-touch-action.js
│   │   │   │   │   ├── css-transitions.js
│   │   │   │   │   ├── css-unicode-bidi.js
│   │   │   │   │   ├── css-unset-value.js
│   │   │   │   │   ├── css-variables.js
│   │   │   │   │   ├── css-when-else.js
│   │   │   │   │   ├── css-widows-orphans.js
│   │   │   │   │   ├── css-width-stretch.js
│   │   │   │   │   ├── css-writing-mode.js
│   │   │   │   │   ├── css-zoom.js
│   │   │   │   │   ├── currentcolor.js
│   │   │   │   │   ├── custom-elements.js
│   │   │   │   │   ├── custom-elementsv1.js
│   │   │   │   │   ├── customevent.js
│   │   │   │   │   ├── customizable-select.js
│   │   │   │   │   ├── datalist.js
│   │   │   │   │   ├── dataset.js
│   │   │   │   │   ├── datauri.js
│   │   │   │   │   ├── date-tolocaledatestring.js
│   │   │   │   │   ├── declarative-shadow-dom.js
│   │   │   │   │   ├── decorators.js
│   │   │   │   │   ├── details.js
│   │   │   │   │   ├── deviceorientation.js
│   │   │   │   │   ├── devicepixelratio.js
│   │   │   │   │   ├── dialog.js
│   │   │   │   │   ├── dispatchevent.js
│   │   │   │   │   ├── dnssec.js
│   │   │   │   │   ├── document-currentscript.js
│   │   │   │   │   ├── document-evaluate-xpath.js
│   │   │   │   │   ├── document-execcommand.js
│   │   │   │   │   ├── documenthead.js
│   │   │   │   │   ├── document-policy.js
│   │   │   │   │   ├── document-scrollingelement.js
│   │   │   │   │   ├── domcontentloaded.js
│   │   │   │   │   ├── dom-manip-convenience.js
│   │   │   │   │   ├── dommatrix.js
│   │   │   │   │   ├── dom-range.js
│   │   │   │   │   ├── do-not-track.js
│   │   │   │   │   ├── download.js
│   │   │   │   │   ├── dragndrop.js
│   │   │   │   │   ├── element-closest.js
│   │   │   │   │   ├── element-from-point.js
│   │   │   │   │   ├── element-scroll-methods.js
│   │   │   │   │   ├── eme.js
│   │   │   │   │   ├── eot.js
│   │   │   │   │   ├── es5.js
│   │   │   │   │   ├── es6-class.js
│   │   │   │   │   ├── es6-generators.js
│   │   │   │   │   ├── es6.js
│   │   │   │   │   ├── es6-module-dynamic-import.js
│   │   │   │   │   ├── es6-module.js
│   │   │   │   │   ├── es6-number.js
│   │   │   │   │   ├── es6-string-includes.js
│   │   │   │   │   ├── eventsource.js
│   │   │   │   │   ├── extended-system-fonts.js
│   │   │   │   │   ├── feature-policy.js
│   │   │   │   │   ├── fetch.js
│   │   │   │   │   ├── fieldset-disabled.js
│   │   │   │   │   ├── fileapi.js
│   │   │   │   │   ├── filereader.js
│   │   │   │   │   ├── filereadersync.js
│   │   │   │   │   ├── filesystem.js
│   │   │   │   │   ├── flac.js
│   │   │   │   │   ├── flexbox-gap.js
│   │   │   │   │   ├── flexbox.js
│   │   │   │   │   ├── flow-root.js
│   │   │   │   │   ├── focusin-focusout-events.js
│   │   │   │   │   ├── fontface.js
│   │   │   │   │   ├── font-family-system-ui.js
│   │   │   │   │   ├── font-feature.js
│   │   │   │   │   ├── font-kerning.js
│   │   │   │   │   ├── font-loading.js
│   │   │   │   │   ├── font-size-adjust.js
│   │   │   │   │   ├── font-smooth.js
│   │   │   │   │   ├── font-unicode-range.js
│   │   │   │   │   ├── font-variant-alternates.js
│   │   │   │   │   ├── font-variant-numeric.js
│   │   │   │   │   ├── form-attribute.js
│   │   │   │   │   ├── forms.js
│   │   │   │   │   ├── form-submit-attributes.js
│   │   │   │   │   ├── form-validation.js
│   │   │   │   │   ├── fullscreen.js
│   │   │   │   │   ├── gamepad.js
│   │   │   │   │   ├── geolocation.js
│   │   │   │   │   ├── getboundingclientrect.js
│   │   │   │   │   ├── getcomputedstyle.js
│   │   │   │   │   ├── getelementsbyclassname.js
│   │   │   │   │   ├── getrandomvalues.js
│   │   │   │   │   ├── gyroscope.js
│   │   │   │   │   ├── hardwareconcurrency.js
│   │   │   │   │   ├── hashchange.js
│   │   │   │   │   ├── heif.js
│   │   │   │   │   ├── hevc.js
│   │   │   │   │   ├── hidden.js
│   │   │   │   │   ├── high-resolution-time.js
│   │   │   │   │   ├── history.js
│   │   │   │   │   ├── html5semantic.js
│   │   │   │   │   ├── html-media-capture.js
│   │   │   │   │   ├── http2.js
│   │   │   │   │   ├── http3.js
│   │   │   │   │   ├── http-live-streaming.js
│   │   │   │   │   ├── iframe-sandbox.js
│   │   │   │   │   ├── iframe-seamless.js
│   │   │   │   │   ├── iframe-srcdoc.js
│   │   │   │   │   ├── imagecapture.js
│   │   │   │   │   ├── ime.js
│   │   │   │   │   ├── img-naturalwidth-naturalheight.js
│   │   │   │   │   ├── import-maps.js
│   │   │   │   │   ├── imports.js
│   │   │   │   │   ├── indeterminate-checkbox.js
│   │   │   │   │   ├── indexeddb2.js
│   │   │   │   │   ├── indexeddb.js
│   │   │   │   │   ├── inline-block.js
│   │   │   │   │   ├── innertext.js
│   │   │   │   │   ├── input-autocomplete-onoff.js
│   │   │   │   │   ├── input-color.js
│   │   │   │   │   ├── input-datetime.js
│   │   │   │   │   ├── input-email-tel-url.js
│   │   │   │   │   ├── input-event.js
│   │   │   │   │   ├── input-file-accept.js
│   │   │   │   │   ├── input-file-directory.js
│   │   │   │   │   ├── input-file-multiple.js
│   │   │   │   │   ├── input-inputmode.js
│   │   │   │   │   ├── input-minlength.js
│   │   │   │   │   ├── input-number.js
│   │   │   │   │   ├── input-pattern.js
│   │   │   │   │   ├── input-placeholder.js
│   │   │   │   │   ├── input-range.js
│   │   │   │   │   ├── input-search.js
│   │   │   │   │   ├── input-selection.js
│   │   │   │   │   ├── insertadjacenthtml.js
│   │   │   │   │   ├── insert-adjacent.js
│   │   │   │   │   ├── internationalization.js
│   │   │   │   │   ├── intersectionobserver.js
│   │   │   │   │   ├── intersectionobserver-v2.js
│   │   │   │   │   ├── intl-pluralrules.js
│   │   │   │   │   ├── intrinsic-width.js
│   │   │   │   │   ├── jpeg2000.js
│   │   │   │   │   ├── jpegxl.js
│   │   │   │   │   ├── jpegxr.js
│   │   │   │   │   ├── json.js
│   │   │   │   │   ├── js-regexp-lookbehind.js
│   │   │   │   │   ├── justify-content-space-evenly.js
│   │   │   │   │   ├── kerning-pairs-ligatures.js
│   │   │   │   │   ├── keyboardevent-charcode.js
│   │   │   │   │   ├── keyboardevent-code.js
│   │   │   │   │   ├── keyboardevent-getmodifierstate.js
│   │   │   │   │   ├── keyboardevent-key.js
│   │   │   │   │   ├── keyboardevent-location.js
│   │   │   │   │   ├── keyboardevent-which.js
│   │   │   │   │   ├── lazyload.js
│   │   │   │   │   ├── let.js
│   │   │   │   │   ├── link-icon-png.js
│   │   │   │   │   ├── link-icon-svg.js
│   │   │   │   │   ├── link-rel-dns-prefetch.js
│   │   │   │   │   ├── link-rel-modulepreload.js
│   │   │   │   │   ├── link-rel-preconnect.js
│   │   │   │   │   ├── link-rel-prefetch.js
│   │   │   │   │   ├── link-rel-preload.js
│   │   │   │   │   ├── link-rel-prerender.js
│   │   │   │   │   ├── loading-lazy-attr.js
│   │   │   │   │   ├── loading-lazy-media.js
│   │   │   │   │   ├── localecompare.js
│   │   │   │   │   ├── magnetometer.js
│   │   │   │   │   ├── matchesselector.js
│   │   │   │   │   ├── matchmedia.js
│   │   │   │   │   ├── mathml.js
│   │   │   │   │   ├── maxlength.js
│   │   │   │   │   ├── mdn-css-backdrop-pseudo-element.js
│   │   │   │   │   ├── mdn-css-unicode-bidi-isolate.js
│   │   │   │   │   ├── mdn-css-unicode-bidi-isolate-override.js
│   │   │   │   │   ├── mdn-css-unicode-bidi-plaintext.js
│   │   │   │   │   ├── mdn-text-decoration-color.js
│   │   │   │   │   ├── mdn-text-decoration-line.js
│   │   │   │   │   ├── mdn-text-decoration-shorthand.js
│   │   │   │   │   ├── mdn-text-decoration-style.js
│   │   │   │   │   ├── mediacapture-fromelement.js
│   │   │   │   │   ├── media-fragments.js
│   │   │   │   │   ├── mediarecorder.js
│   │   │   │   │   ├── mediasource.js
│   │   │   │   │   ├── menu.js
│   │   │   │   │   ├── meta-theme-color.js
│   │   │   │   │   ├── meter.js
│   │   │   │   │   ├── midi.js
│   │   │   │   │   ├── minmaxwh.js
│   │   │   │   │   ├── mp3.js
│   │   │   │   │   ├── mpeg4.js
│   │   │   │   │   ├── mpeg-dash.js
│   │   │   │   │   ├── multibackgrounds.js
│   │   │   │   │   ├── multicolumn.js
│   │   │   │   │   ├── mutation-events.js
│   │   │   │   │   ├── mutationobserver.js
│   │   │   │   │   ├── namevalue-storage.js
│   │   │   │   │   ├── native-filesystem-api.js
│   │   │   │   │   ├── nav-timing.js
│   │   │   │   │   ├── netinfo.js
│   │   │   │   │   ├── notifications.js
│   │   │   │   │   ├── object-entries.js
│   │   │   │   │   ├── object-fit.js
│   │   │   │   │   ├── object-observe.js
│   │   │   │   │   ├── objectrtc.js
│   │   │   │   │   ├── object-values.js
│   │   │   │   │   ├── offline-apps.js
│   │   │   │   │   ├── offscreencanvas.js
│   │   │   │   │   ├── ogg-vorbis.js
│   │   │   │   │   ├── ogv.js
│   │   │   │   │   ├── ol-reversed.js
│   │   │   │   │   ├── once-event-listener.js
│   │   │   │   │   ├── online-status.js
│   │   │   │   │   ├── opus.js
│   │   │   │   │   ├── orientation-sensor.js
│   │   │   │   │   ├── outline.js
│   │   │   │   │   ├── pad-start-end.js
│   │   │   │   │   ├── page-transition-events.js
│   │   │   │   │   ├── pagevisibility.js
│   │   │   │   │   ├── passive-event-listener.js
│   │   │   │   │   ├── passkeys.js
│   │   │   │   │   ├── passwordrules.js
│   │   │   │   │   ├── path2d.js
│   │   │   │   │   ├── payment-request.js
│   │   │   │   │   ├── pdf-viewer.js
│   │   │   │   │   ├── permissions-api.js
│   │   │   │   │   ├── permissions-policy.js
│   │   │   │   │   ├── picture-in-picture.js
│   │   │   │   │   ├── picture.js
│   │   │   │   │   ├── ping.js
│   │   │   │   │   ├── png-alpha.js
│   │   │   │   │   ├── pointer-events.js
│   │   │   │   │   ├── pointer.js
│   │   │   │   │   ├── pointerlock.js
│   │   │   │   │   ├── portals.js
│   │   │   │   │   ├── prefers-color-scheme.js
│   │   │   │   │   ├── prefers-reduced-motion.js
│   │   │   │   │   ├── progress.js
│   │   │   │   │   ├── promise-finally.js
│   │   │   │   │   ├── promises.js
│   │   │   │   │   ├── proximity.js
│   │   │   │   │   ├── proxy.js
│   │   │   │   │   ├── publickeypinning.js
│   │   │   │   │   ├── push-api.js
│   │   │   │   │   ├── queryselector.js
│   │   │   │   │   ├── readonly-attr.js
│   │   │   │   │   ├── referrer-policy.js
│   │   │   │   │   ├── registerprotocolhandler.js
│   │   │   │   │   ├── rellist.js
│   │   │   │   │   ├── rel-noopener.js
│   │   │   │   │   ├── rel-noreferrer.js
│   │   │   │   │   ├── rem.js
│   │   │   │   │   ├── requestanimationframe.js
│   │   │   │   │   ├── requestidlecallback.js
│   │   │   │   │   ├── resizeobserver.js
│   │   │   │   │   ├── resource-timing.js
│   │   │   │   │   ├── rest-parameters.js
│   │   │   │   │   ├── rtcpeerconnection.js
│   │   │   │   │   ├── ruby.js
│   │   │   │   │   ├── run-in.js
│   │   │   │   │   ├── same-site-cookie-attribute.js
│   │   │   │   │   ├── screen-orientation.js
│   │   │   │   │   ├── script-async.js
│   │   │   │   │   ├── script-defer.js
│   │   │   │   │   ├── scrollintoviewifneeded.js
│   │   │   │   │   ├── scrollintoview.js
│   │   │   │   │   ├── sdch.js
│   │   │   │   │   ├── selection-api.js
│   │   │   │   │   ├── server-timing.js
│   │   │   │   │   ├── serviceworkers.js
│   │   │   │   │   ├── setimmediate.js
│   │   │   │   │   ├── shadowdom.js
│   │   │   │   │   ├── shadowdomv1.js
│   │   │   │   │   ├── sharedarraybuffer.js
│   │   │   │   │   ├── sharedworkers.js
│   │   │   │   │   ├── sni.js
│   │   │   │   │   ├── spdy.js
│   │   │   │   │   ├── speech-recognition.js
│   │   │   │   │   ├── speech-synthesis.js
│   │   │   │   │   ├── spellcheck-attribute.js
│   │   │   │   │   ├── sql-storage.js
│   │   │   │   │   ├── srcset.js
│   │   │   │   │   ├── stream.js
│   │   │   │   │   ├── streams.js
│   │   │   │   │   ├── stricttransportsecurity.js
│   │   │   │   │   ├── style-scoped.js
│   │   │   │   │   ├── subresource-bundling.js
│   │   │   │   │   ├── subresource-integrity.js
│   │   │   │   │   ├── svg-css.js
│   │   │   │   │   ├── svg-filters.js
│   │   │   │   │   ├── svg-fonts.js
│   │   │   │   │   ├── svg-fragment.js
│   │   │   │   │   ├── svg-html5.js
│   │   │   │   │   ├── svg-html.js
│   │   │   │   │   ├── svg-img.js
│   │   │   │   │   ├── svg.js
│   │   │   │   │   ├── svg-smil.js
│   │   │   │   │   ├── sxg.js
│   │   │   │   │   ├── tabindex-attr.js
│   │   │   │   │   ├── template.js
│   │   │   │   │   ├── template-literals.js
│   │   │   │   │   ├── temporal.js
│   │   │   │   │   ├── testfeat.js
│   │   │   │   │   ├── textcontent.js
│   │   │   │   │   ├── text-decoration.js
│   │   │   │   │   ├── text-emphasis.js
│   │   │   │   │   ├── textencoder.js
│   │   │   │   │   ├── text-overflow.js
│   │   │   │   │   ├── text-size-adjust.js
│   │   │   │   │   ├── text-stroke.js
│   │   │   │   │   ├── tls1-1.js
│   │   │   │   │   ├── tls1-2.js
│   │   │   │   │   ├── tls1-3.js
│   │   │   │   │   ├── touch.js
│   │   │   │   │   ├── transforms2d.js
│   │   │   │   │   ├── transforms3d.js
│   │   │   │   │   ├── trusted-types.js
│   │   │   │   │   ├── ttf.js
│   │   │   │   │   ├── typedarrays.js
│   │   │   │   │   ├── u2f.js
│   │   │   │   │   ├── unhandledrejection.js
│   │   │   │   │   ├── upgradeinsecurerequests.js
│   │   │   │   │   ├── url.js
│   │   │   │   │   ├── url-scroll-to-text-fragment.js
│   │   │   │   │   ├── urlsearchparams.js
│   │   │   │   │   ├── user-select-none.js
│   │   │   │   │   ├── user-timing.js
│   │   │   │   │   ├── use-strict.js
│   │   │   │   │   ├── variable-fonts.js
│   │   │   │   │   ├── vector-effect.js
│   │   │   │   │   ├── vibration.js
│   │   │   │   │   ├── video.js
│   │   │   │   │   ├── videotracks.js
│   │   │   │   │   ├── viewport-units.js
│   │   │   │   │   ├── viewport-unit-variants.js
│   │   │   │   │   ├── view-transitions.js
│   │   │   │   │   ├── wai-aria.js
│   │   │   │   │   ├── wake-lock.js
│   │   │   │   │   ├── wasm-bigint.js
│   │   │   │   │   ├── wasm-bulk-memory.js
│   │   │   │   │   ├── wasm-extended-const.js
│   │   │   │   │   ├── wasm-gc.js
│   │   │   │   │   ├── wasm.js
│   │   │   │   │   ├── wasm-multi-memory.js
│   │   │   │   │   ├── wasm-multi-value.js
│   │   │   │   │   ├── wasm-mutable-globals.js
│   │   │   │   │   ├── wasm-nontrapping-fptoint.js
│   │   │   │   │   ├── wasm-reference-types.js
│   │   │   │   │   ├── wasm-relaxed-simd.js
│   │   │   │   │   ├── wasm-signext.js
│   │   │   │   │   ├── wasm-simd.js
│   │   │   │   │   ├── wasm-tail-calls.js
│   │   │   │   │   ├── wasm-threads.js
│   │   │   │   │   ├── wav.js
│   │   │   │   │   ├── wbr-element.js
│   │   │   │   │   ├── web-animation.js
│   │   │   │   │   ├── web-app-manifest.js
│   │   │   │   │   ├── webauthn.js
│   │   │   │   │   ├── web-bluetooth.js
│   │   │   │   │   ├── webcodecs.js
│   │   │   │   │   ├── webgl2.js
│   │   │   │   │   ├── webgl.js
│   │   │   │   │   ├── webgpu.js
│   │   │   │   │   ├── webhid.js
│   │   │   │   │   ├── webkit-user-drag.js
│   │   │   │   │   ├── webm.js
│   │   │   │   │   ├── webnfc.js
│   │   │   │   │   ├── webp.js
│   │   │   │   │   ├── web-serial.js
│   │   │   │   │   ├── web-share.js
│   │   │   │   │   ├── websockets.js
│   │   │   │   │   ├── webtransport.js
│   │   │   │   │   ├── webusb.js
│   │   │   │   │   ├── webvr.js
│   │   │   │   │   ├── webvtt.js
│   │   │   │   │   ├── webworkers.js
│   │   │   │   │   ├── webxr.js
│   │   │   │   │   ├── will-change.js
│   │   │   │   │   ├── woff2.js
│   │   │   │   │   ├── woff.js
│   │   │   │   │   ├── word-break.js
│   │   │   │   │   ├── wordwrap.js
│   │   │   │   │   ├── x-doc-messaging.js
│   │   │   │   │   ├── x-frame-options.js
│   │   │   │   │   ├── xhr2.js
│   │   │   │   │   ├── xhtml.js
│   │   │   │   │   ├── xhtmlsmil.js
│   │   │   │   │   ├── xml-serializer.js
│   │   │   │   │   └── zstd.js
│   │   │   │   ├── features.js
│   │   │   │   └── regions
│   │   │   │       ├── AD.js
│   │   │   │       ├── AE.js
│   │   │   │       ├── AF.js
│   │   │   │       ├── AG.js
│   │   │   │       ├── AI.js
│   │   │   │       ├── AL.js
│   │   │   │       ├── alt-af.js
│   │   │   │       ├── alt-an.js
│   │   │   │       ├── alt-as.js
│   │   │   │       ├── alt-eu.js
│   │   │   │       ├── alt-na.js
│   │   │   │       ├── alt-oc.js
│   │   │   │       ├── alt-sa.js
│   │   │   │       ├── alt-ww.js
│   │   │   │       ├── AM.js
│   │   │   │       ├── AO.js
│   │   │   │       ├── AR.js
│   │   │   │       ├── AS.js
│   │   │   │       ├── AT.js
│   │   │   │       ├── AU.js
│   │   │   │       ├── AW.js
│   │   │   │       ├── AX.js
│   │   │   │       ├── AZ.js
│   │   │   │       ├── BA.js
│   │   │   │       ├── BB.js
│   │   │   │       ├── BD.js
│   │   │   │       ├── BE.js
│   │   │   │       ├── BF.js
│   │   │   │       ├── BG.js
│   │   │   │       ├── BH.js
│   │   │   │       ├── BI.js
│   │   │   │       ├── BJ.js
│   │   │   │       ├── BM.js
│   │   │   │       ├── BN.js
│   │   │   │       ├── BO.js
│   │   │   │       ├── BR.js
│   │   │   │       ├── BS.js
│   │   │   │       ├── BT.js
│   │   │   │       ├── BW.js
│   │   │   │       ├── BY.js
│   │   │   │       ├── BZ.js
│   │   │   │       ├── CA.js
│   │   │   │       ├── CD.js
│   │   │   │       ├── CF.js
│   │   │   │       ├── CG.js
│   │   │   │       ├── CH.js
│   │   │   │       ├── CI.js
│   │   │   │       ├── CK.js
│   │   │   │       ├── CL.js
│   │   │   │       ├── CM.js
│   │   │   │       ├── CN.js
│   │   │   │       ├── CO.js
│   │   │   │       ├── CR.js
│   │   │   │       ├── CU.js
│   │   │   │       ├── CV.js
│   │   │   │       ├── CX.js
│   │   │   │       ├── CY.js
│   │   │   │       ├── CZ.js
│   │   │   │       ├── DE.js
│   │   │   │       ├── DJ.js
│   │   │   │       ├── DK.js
│   │   │   │       ├── DM.js
│   │   │   │       ├── DO.js
│   │   │   │       ├── DZ.js
│   │   │   │       ├── EC.js
│   │   │   │       ├── EE.js
│   │   │   │       ├── EG.js
│   │   │   │       ├── ER.js
│   │   │   │       ├── ES.js
│   │   │   │       ├── ET.js
│   │   │   │       ├── FI.js
│   │   │   │       ├── FJ.js
│   │   │   │       ├── FK.js
│   │   │   │       ├── FM.js
│   │   │   │       ├── FO.js
│   │   │   │       ├── FR.js
│   │   │   │       ├── GA.js
│   │   │   │       ├── GB.js
│   │   │   │       ├── GD.js
│   │   │   │       ├── GE.js
│   │   │   │       ├── GF.js
│   │   │   │       ├── GG.js
│   │   │   │       ├── GH.js
│   │   │   │       ├── GI.js
│   │   │   │       ├── GL.js
│   │   │   │       ├── GM.js
│   │   │   │       ├── GN.js
│   │   │   │       ├── GP.js
│   │   │   │       ├── GQ.js
│   │   │   │       ├── GR.js
│   │   │   │       ├── GT.js
│   │   │   │       ├── GU.js
│   │   │   │       ├── GW.js
│   │   │   │       ├── GY.js
│   │   │   │       ├── HK.js
│   │   │   │       ├── HN.js
│   │   │   │       ├── HR.js
│   │   │   │       ├── HT.js
│   │   │   │       ├── HU.js
│   │   │   │       ├── ID.js
│   │   │   │       ├── IE.js
│   │   │   │       ├── IL.js
│   │   │   │       ├── IM.js
│   │   │   │       ├── IN.js
│   │   │   │       ├── IQ.js
│   │   │   │       ├── IR.js
│   │   │   │       ├── IS.js
│   │   │   │       ├── IT.js
│   │   │   │       ├── JE.js
│   │   │   │       ├── JM.js
│   │   │   │       ├── JO.js
│   │   │   │       ├── JP.js
│   │   │   │       ├── KE.js
│   │   │   │       ├── KG.js
│   │   │   │       ├── KH.js
│   │   │   │       ├── KI.js
│   │   │   │       ├── KM.js
│   │   │   │       ├── KN.js
│   │   │   │       ├── KP.js
│   │   │   │       ├── KR.js
│   │   │   │       ├── KW.js
│   │   │   │       ├── KY.js
│   │   │   │       ├── KZ.js
│   │   │   │       ├── LA.js
│   │   │   │       ├── LB.js
│   │   │   │       ├── LC.js
│   │   │   │       ├── LI.js
│   │   │   │       ├── LK.js
│   │   │   │       ├── LR.js
│   │   │   │       ├── LS.js
│   │   │   │       ├── LT.js
│   │   │   │       ├── LU.js
│   │   │   │       ├── LV.js
│   │   │   │       ├── LY.js
│   │   │   │       ├── MA.js
│   │   │   │       ├── MC.js
│   │   │   │       ├── MD.js
│   │   │   │       ├── ME.js
│   │   │   │       ├── MG.js
│   │   │   │       ├── MH.js
│   │   │   │       ├── MK.js
│   │   │   │       ├── ML.js
│   │   │   │       ├── MM.js
│   │   │   │       ├── MN.js
│   │   │   │       ├── MO.js
│   │   │   │       ├── MP.js
│   │   │   │       ├── MQ.js
│   │   │   │       ├── MR.js
│   │   │   │       ├── MS.js
│   │   │   │       ├── MT.js
│   │   │   │       ├── MU.js
│   │   │   │       ├── MV.js
│   │   │   │       ├── MW.js
│   │   │   │       ├── MX.js
│   │   │   │       ├── MY.js
│   │   │   │       ├── MZ.js
│   │   │   │       ├── NA.js
│   │   │   │       ├── NC.js
│   │   │   │       ├── NE.js
│   │   │   │       ├── NF.js
│   │   │   │       ├── NG.js
│   │   │   │       ├── NI.js
│   │   │   │       ├── NL.js
│   │   │   │       ├── NO.js
│   │   │   │       ├── NP.js
│   │   │   │       ├── NR.js
│   │   │   │       ├── NU.js
│   │   │   │       ├── NZ.js
│   │   │   │       ├── OM.js
│   │   │   │       ├── PA.js
│   │   │   │       ├── PE.js
│   │   │   │       ├── PF.js
│   │   │   │       ├── PG.js
│   │   │   │       ├── PH.js
│   │   │   │       ├── PK.js
│   │   │   │       ├── PL.js
│   │   │   │       ├── PM.js
│   │   │   │       ├── PN.js
│   │   │   │       ├── PR.js
│   │   │   │       ├── PS.js
│   │   │   │       ├── PT.js
│   │   │   │       ├── PW.js
│   │   │   │       ├── PY.js
│   │   │   │       ├── QA.js
│   │   │   │       ├── RE.js
│   │   │   │       ├── RO.js
│   │   │   │       ├── RS.js
│   │   │   │       ├── RU.js
│   │   │   │       ├── RW.js
│   │   │   │       ├── SA.js
│   │   │   │       ├── SB.js
│   │   │   │       ├── SC.js
│   │   │   │       ├── SD.js
│   │   │   │       ├── SE.js
│   │   │   │       ├── SG.js
│   │   │   │       ├── SH.js
│   │   │   │       ├── SI.js
│   │   │   │       ├── SK.js
│   │   │   │       ├── SL.js
│   │   │   │       ├── SM.js
│   │   │   │       ├── SN.js
│   │   │   │       ├── SO.js
│   │   │   │       ├── SR.js
│   │   │   │       ├── ST.js
│   │   │   │       ├── SV.js
│   │   │   │       ├── SY.js
│   │   │   │       ├── SZ.js
│   │   │   │       ├── TC.js
│   │   │   │       ├── TD.js
│   │   │   │       ├── TG.js
│   │   │   │       ├── TH.js
│   │   │   │       ├── TJ.js
│   │   │   │       ├── TL.js
│   │   │   │       ├── TM.js
│   │   │   │       ├── TN.js
│   │   │   │       ├── TO.js
│   │   │   │       ├── TR.js
│   │   │   │       ├── TT.js
│   │   │   │       ├── TV.js
│   │   │   │       ├── TW.js
│   │   │   │       ├── TZ.js
│   │   │   │       ├── UA.js
│   │   │   │       ├── UG.js
│   │   │   │       ├── US.js
│   │   │   │       ├── UY.js
│   │   │   │       ├── UZ.js
│   │   │   │       ├── VA.js
│   │   │   │       ├── VC.js
│   │   │   │       ├── VE.js
│   │   │   │       ├── VG.js
│   │   │   │       ├── VI.js
│   │   │   │       ├── VN.js
│   │   │   │       ├── VU.js
│   │   │   │       ├── WF.js
│   │   │   │       ├── WS.js
│   │   │   │       ├── YE.js
│   │   │   │       ├── YT.js
│   │   │   │       ├── ZA.js
│   │   │   │       ├── ZM.js
│   │   │   │       └── ZW.js
│   │   │   ├── dist
│   │   │   │   ├── lib
│   │   │   │   │   ├── statuses.js
│   │   │   │   │   └── supported.js
│   │   │   │   └── unpacker
│   │   │   │       ├── agents.js
│   │   │   │       ├── browsers.js
│   │   │   │       ├── browserVersions.js
│   │   │   │       ├── feature.js
│   │   │   │       ├── features.js
│   │   │   │       ├── index.js
│   │   │   │       └── region.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── chart.js
│   │   │   ├── auto
│   │   │   │   ├── auto.cjs
│   │   │   │   ├── auto.d.ts
│   │   │   │   ├── auto.js
│   │   │   │   └── package.json
│   │   │   ├── dist
│   │   │   │   ├── chart.cjs
│   │   │   │   ├── chart.cjs.map
│   │   │   │   ├── chart.js
│   │   │   │   ├── chart.js.map
│   │   │   │   ├── chart.umd.js
│   │   │   │   ├── chart.umd.js.map
│   │   │   │   ├── chart.umd.min.js
│   │   │   │   ├── chart.umd.min.js.map
│   │   │   │   ├── chunks
│   │   │   │   │   ├── helpers.dataset.cjs
│   │   │   │   │   ├── helpers.dataset.cjs.map
│   │   │   │   │   ├── helpers.dataset.js
│   │   │   │   │   └── helpers.dataset.js.map
│   │   │   │   ├── controllers
│   │   │   │   │   ├── controller.bar.d.ts
│   │   │   │   │   ├── controller.bubble.d.ts
│   │   │   │   │   ├── controller.doughnut.d.ts
│   │   │   │   │   ├── controller.line.d.ts
│   │   │   │   │   ├── controller.pie.d.ts
│   │   │   │   │   ├── controller.polarArea.d.ts
│   │   │   │   │   ├── controller.radar.d.ts
│   │   │   │   │   ├── controller.scatter.d.ts
│   │   │   │   │   └── index.d.ts
│   │   │   │   ├── core
│   │   │   │   │   ├── core.adapters.d.ts
│   │   │   │   │   ├── core.animation.d.ts
│   │   │   │   │   ├── core.animations.defaults.d.ts
│   │   │   │   │   ├── core.animations.d.ts
│   │   │   │   │   ├── core.animator.d.ts
│   │   │   │   │   ├── core.config.d.ts
│   │   │   │   │   ├── core.controller.d.ts
│   │   │   │   │   ├── core.datasetController.d.ts
│   │   │   │   │   ├── core.defaults.d.ts
│   │   │   │   │   ├── core.element.d.ts
│   │   │   │   │   ├── core.interaction.d.ts
│   │   │   │   │   ├── core.layouts.defaults.d.ts
│   │   │   │   │   ├── core.layouts.d.ts
│   │   │   │   │   ├── core.plugins.d.ts
│   │   │   │   │   ├── core.registry.d.ts
│   │   │   │   │   ├── core.scale.autoskip.d.ts
│   │   │   │   │   ├── core.scale.defaults.d.ts
│   │   │   │   │   ├── core.scale.d.ts
│   │   │   │   │   ├── core.ticks.d.ts
│   │   │   │   │   ├── core.typedRegistry.d.ts
│   │   │   │   │   └── index.d.ts
│   │   │   │   ├── elements
│   │   │   │   │   ├── element.arc.d.ts
│   │   │   │   │   ├── element.bar.d.ts
│   │   │   │   │   ├── element.line.d.ts
│   │   │   │   │   ├── element.point.d.ts
│   │   │   │   │   └── index.d.ts
│   │   │   │   ├── helpers
│   │   │   │   │   ├── helpers.canvas.d.ts
│   │   │   │   │   ├── helpers.collection.d.ts
│   │   │   │   │   ├── helpers.color.d.ts
│   │   │   │   │   ├── helpers.config.d.ts
│   │   │   │   │   ├── helpers.config.types.d.ts
│   │   │   │   │   ├── helpers.core.d.ts
│   │   │   │   │   ├── helpers.curve.d.ts
│   │   │   │   │   ├── helpers.dataset.d.ts
│   │   │   │   │   ├── helpers.dom.d.ts
│   │   │   │   │   ├── helpers.easing.d.ts
│   │   │   │   │   ├── helpers.extras.d.ts
│   │   │   │   │   ├── helpers.interpolation.d.ts
│   │   │   │   │   ├── helpers.intl.d.ts
│   │   │   │   │   ├── helpers.math.d.ts
│   │   │   │   │   ├── helpers.options.d.ts
│   │   │   │   │   ├── helpers.rtl.d.ts
│   │   │   │   │   ├── helpers.segment.d.ts
│   │   │   │   │   └── index.d.ts
│   │   │   │   ├── helpers.cjs
│   │   │   │   ├── helpers.cjs.map
│   │   │   │   ├── helpers.js
│   │   │   │   ├── helpers.js.map
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.umd.d.ts
│   │   │   │   ├── platform
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── platform.base.d.ts
│   │   │   │   │   ├── platform.basic.d.ts
│   │   │   │   │   └── platform.dom.d.ts
│   │   │   │   ├── plugins
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── plugin.colors.d.ts
│   │   │   │   │   ├── plugin.decimation.d.ts
│   │   │   │   │   ├── plugin.filler
│   │   │   │   │   │   ├── filler.drawing.d.ts
│   │   │   │   │   │   ├── filler.helper.d.ts
│   │   │   │   │   │   ├── filler.options.d.ts
│   │   │   │   │   │   ├── filler.segment.d.ts
│   │   │   │   │   │   ├── filler.target.d.ts
│   │   │   │   │   │   ├── filler.target.stack.d.ts
│   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   └── simpleArc.d.ts
│   │   │   │   │   ├── plugin.legend.d.ts
│   │   │   │   │   ├── plugin.subtitle.d.ts
│   │   │   │   │   ├── plugin.title.d.ts
│   │   │   │   │   └── plugin.tooltip.d.ts
│   │   │   │   ├── scales
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── scale.category.d.ts
│   │   │   │   │   ├── scale.linearbase.d.ts
│   │   │   │   │   ├── scale.linear.d.ts
│   │   │   │   │   ├── scale.logarithmic.d.ts
│   │   │   │   │   ├── scale.radialLinear.d.ts
│   │   │   │   │   ├── scale.time.d.ts
│   │   │   │   │   └── scale.timeseries.d.ts
│   │   │   │   ├── types
│   │   │   │   │   ├── animation.d.ts
│   │   │   │   │   ├── basic.d.ts
│   │   │   │   │   ├── color.d.ts
│   │   │   │   │   ├── geometric.d.ts
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── layout.d.ts
│   │   │   │   │   └── utils.d.ts
│   │   │   │   └── types.d.ts
│   │   │   ├── helpers
│   │   │   │   ├── helpers.cjs
│   │   │   │   ├── helpers.d.ts
│   │   │   │   ├── helpers.js
│   │   │   │   └── package.json
│   │   │   ├── LICENSE.md
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── chokidar
│   │   │   ├── index.js
│   │   │   ├── lib
│   │   │   │   ├── constants.js
│   │   │   │   ├── fsevents-handler.js
│   │   │   │   └── nodefs-handler.js
│   │   │   ├── LICENSE
│   │   │   ├── node_modules
│   │   │   │   └── glob-parent
│   │   │   │       ├── CHANGELOG.md
│   │   │   │       ├── index.js
│   │   │   │       ├── LICENSE
│   │   │   │       ├── package.json
│   │   │   │       └── README.md
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── types
│   │   │       └── index.d.ts
│   │   ├── commander
│   │   │   ├── CHANGELOG.md
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── Readme.md
│   │   │   └── typings
│   │   │       └── index.d.ts
│   │   ├── cssesc
│   │   │   ├── bin
│   │   │   │   └── cssesc
│   │   │   ├── cssesc.js
│   │   │   ├── LICENSE-MIT.txt
│   │   │   ├── man
│   │   │   │   └── cssesc.1
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── didyoumean
│   │   │   ├── didYouMean-1.2.1.js
│   │   │   ├── didYouMean-1.2.1.min.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── dlv
│   │   │   ├── dist
│   │   │   │   ├── dlv.es.js
│   │   │   │   ├── dlv.es.js.map
│   │   │   │   ├── dlv.js
│   │   │   │   ├── dlv.js.map
│   │   │   │   ├── dlv.umd.js
│   │   │   │   └── dlv.umd.js.map
│   │   │   ├── index.js
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── electron-to-chromium
│   │   │   ├── chromium-versions.js
│   │   │   ├── chromium-versions.json
│   │   │   ├── full-chromium-versions.js
│   │   │   ├── full-chromium-versions.json
│   │   │   ├── full-versions.js
│   │   │   ├── full-versions.json
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── versions.js
│   │   │   └── versions.json
│   │   ├── @esbuild
│   │   │   └── linux-x64
│   │   │       ├── bin
│   │   │       │   └── esbuild
│   │   │       ├── package.json
│   │   │       └── README.md
│   │   ├── esbuild
│   │   │   ├── bin
│   │   │   │   └── esbuild
│   │   │   ├── install.js
│   │   │   ├── lib
│   │   │   │   ├── main.d.ts
│   │   │   │   └── main.js
│   │   │   ├── LICENSE.md
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── escalade
│   │   │   ├── dist
│   │   │   │   ├── index.js
│   │   │   │   └── index.mjs
│   │   │   ├── index.d.mts
│   │   │   ├── index.d.ts
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   ├── readme.md
│   │   │   └── sync
│   │   │       ├── index.d.mts
│   │   │       ├── index.d.ts
│   │   │       ├── index.js
│   │   │       └── index.mjs
│   │   ├── es-errors
│   │   │   ├── CHANGELOG.md
│   │   │   ├── eval.d.ts
│   │   │   ├── eval.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── range.d.ts
│   │   │   ├── range.js
│   │   │   ├── README.md
│   │   │   ├── ref.d.ts
│   │   │   ├── ref.js
│   │   │   ├── syntax.d.ts
│   │   │   ├── syntax.js
│   │   │   ├── test
│   │   │   │   └── index.js
│   │   │   ├── tsconfig.json
│   │   │   ├── type.d.ts
│   │   │   ├── type.js
│   │   │   ├── uri.d.ts
│   │   │   └── uri.js
│   │   ├── fast-glob
│   │   │   ├── LICENSE
│   │   │   ├── node_modules
│   │   │   │   └── glob-parent
│   │   │   │       ├── CHANGELOG.md
│   │   │   │       ├── index.js
│   │   │   │       ├── LICENSE
│   │   │   │       ├── package.json
│   │   │   │       └── README.md
│   │   │   ├── out
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   ├── managers
│   │   │   │   │   ├── tasks.d.ts
│   │   │   │   │   └── tasks.js
│   │   │   │   ├── providers
│   │   │   │   │   ├── async.d.ts
│   │   │   │   │   ├── async.js
│   │   │   │   │   ├── filters
│   │   │   │   │   │   ├── deep.d.ts
│   │   │   │   │   │   ├── deep.js
│   │   │   │   │   │   ├── entry.d.ts
│   │   │   │   │   │   ├── entry.js
│   │   │   │   │   │   ├── error.d.ts
│   │   │   │   │   │   └── error.js
│   │   │   │   │   ├── matchers
│   │   │   │   │   │   ├── matcher.d.ts
│   │   │   │   │   │   ├── matcher.js
│   │   │   │   │   │   ├── partial.d.ts
│   │   │   │   │   │   └── partial.js
│   │   │   │   │   ├── provider.d.ts
│   │   │   │   │   ├── provider.js
│   │   │   │   │   ├── stream.d.ts
│   │   │   │   │   ├── stream.js
│   │   │   │   │   ├── sync.d.ts
│   │   │   │   │   ├── sync.js
│   │   │   │   │   └── transformers
│   │   │   │   │       ├── entry.d.ts
│   │   │   │   │       └── entry.js
│   │   │   │   ├── readers
│   │   │   │   │   ├── async.d.ts
│   │   │   │   │   ├── async.js
│   │   │   │   │   ├── reader.d.ts
│   │   │   │   │   ├── reader.js
│   │   │   │   │   ├── stream.d.ts
│   │   │   │   │   ├── stream.js
│   │   │   │   │   ├── sync.d.ts
│   │   │   │   │   └── sync.js
│   │   │   │   ├── settings.d.ts
│   │   │   │   ├── settings.js
│   │   │   │   ├── types
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   └── index.js
│   │   │   │   └── utils
│   │   │   │       ├── array.d.ts
│   │   │   │       ├── array.js
│   │   │   │       ├── errno.d.ts
│   │   │   │       ├── errno.js
│   │   │   │       ├── fs.d.ts
│   │   │   │       ├── fs.js
│   │   │   │       ├── index.d.ts
│   │   │   │       ├── index.js
│   │   │   │       ├── path.d.ts
│   │   │   │       ├── path.js
│   │   │   │       ├── pattern.d.ts
│   │   │   │       ├── pattern.js
│   │   │   │       ├── stream.d.ts
│   │   │   │       ├── stream.js
│   │   │   │       ├── string.d.ts
│   │   │   │       └── string.js
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── fastq
│   │   │   ├── bench.js
│   │   │   ├── eslint.config.js
│   │   │   ├── example.js
│   │   │   ├── example.mjs
│   │   │   ├── index.d.ts
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── queue.js
│   │   │   ├── README.md
│   │   │   ├── SECURITY.md
│   │   │   └── test
│   │   │       ├── example.ts
│   │   │       ├── promise.js
│   │   │       ├── test.js
│   │   │       └── tsconfig.json
│   │   ├── fill-range
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── fraction.js
│   │   │   ├── CHANGELOG.md
│   │   │   ├── dist
│   │   │   │   ├── fraction.js
│   │   │   │   ├── fraction.min.js
│   │   │   │   └── fraction.mjs
│   │   │   ├── examples
│   │   │   │   ├── angles.js
│   │   │   │   ├── approx.js
│   │   │   │   ├── egyptian.js
│   │   │   │   ├── hesse-convergence.js
│   │   │   │   ├── integrate.js
│   │   │   │   ├── ratio-chain.js
│   │   │   │   ├── rational-pow.js
│   │   │   │   ├── tape-measure.js
│   │   │   │   ├── toFraction.js
│   │   │   │   └── valueOfPi.js
│   │   │   ├── fraction.d.mts
│   │   │   ├── fraction.d.ts
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── src
│   │   │   │   └── fraction.js
│   │   │   └── tests
│   │   │       └── fraction.test.js
│   │   ├── function-bind
│   │   │   ├── CHANGELOG.md
│   │   │   ├── implementation.js
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── test
│   │   │       └── index.js
│   │   ├── glob-parent
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── hasown
│   │   │   ├── CHANGELOG.md
│   │   │   ├── eslint.config.mjs
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── tsconfig.json
│   │   ├── is-binary-path
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   └── readme.md
│   │   ├── is-core-module
│   │   │   ├── CHANGELOG.md
│   │   │   ├── core.json
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── test
│   │   │       └── index.js
│   │   ├── is-extglob
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── is-glob
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── is-number
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── jiti
│   │   │   ├── bin
│   │   │   │   └── jiti.js
│   │   │   ├── dist
│   │   │   │   ├── babel.d.ts
│   │   │   │   ├── babel.js
│   │   │   │   ├── jiti.d.ts
│   │   │   │   ├── jiti.js
│   │   │   │   ├── plugins
│   │   │   │   │   ├── babel-plugin-transform-import-meta.d.ts
│   │   │   │   │   └── import-meta-env.d.ts
│   │   │   │   ├── types.d.ts
│   │   │   │   └── utils.d.ts
│   │   │   ├── lib
│   │   │   │   └── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── register.js
│   │   ├── @jridgewell
│   │   │   ├── gen-mapping
│   │   │   │   ├── dist
│   │   │   │   │   ├── gen-mapping.mjs
│   │   │   │   │   ├── gen-mapping.mjs.map
│   │   │   │   │   ├── gen-mapping.umd.js
│   │   │   │   │   ├── gen-mapping.umd.js.map
│   │   │   │   │   └── types
│   │   │   │   │       ├── gen-mapping.d.ts
│   │   │   │   │       ├── set-array.d.ts
│   │   │   │   │       ├── sourcemap-segment.d.ts
│   │   │   │   │       └── types.d.ts
│   │   │   │   ├── LICENSE
│   │   │   │   ├── package.json
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── gen-mapping.ts
│   │   │   │   │   ├── set-array.ts
│   │   │   │   │   ├── sourcemap-segment.ts
│   │   │   │   │   └── types.ts
│   │   │   │   └── types
│   │   │   │       ├── gen-mapping.d.cts
│   │   │   │       ├── gen-mapping.d.cts.map
│   │   │   │       ├── gen-mapping.d.mts
│   │   │   │       ├── gen-mapping.d.mts.map
│   │   │   │       ├── set-array.d.cts
│   │   │   │       ├── set-array.d.cts.map
│   │   │   │       ├── set-array.d.mts
│   │   │   │       ├── set-array.d.mts.map
│   │   │   │       ├── sourcemap-segment.d.cts
│   │   │   │       ├── sourcemap-segment.d.cts.map
│   │   │   │       ├── sourcemap-segment.d.mts
│   │   │   │       ├── sourcemap-segment.d.mts.map
│   │   │   │       ├── types.d.cts
│   │   │   │       ├── types.d.cts.map
│   │   │   │       ├── types.d.mts
│   │   │   │       └── types.d.mts.map
│   │   │   ├── resolve-uri
│   │   │   │   ├── dist
│   │   │   │   │   ├── resolve-uri.mjs
│   │   │   │   │   ├── resolve-uri.mjs.map
│   │   │   │   │   ├── resolve-uri.umd.js
│   │   │   │   │   ├── resolve-uri.umd.js.map
│   │   │   │   │   └── types
│   │   │   │   │       └── resolve-uri.d.ts
│   │   │   │   ├── LICENSE
│   │   │   │   ├── package.json
│   │   │   │   └── README.md
│   │   │   ├── sourcemap-codec
│   │   │   │   ├── dist
│   │   │   │   │   ├── sourcemap-codec.mjs
│   │   │   │   │   ├── sourcemap-codec.mjs.map
│   │   │   │   │   ├── sourcemap-codec.umd.js
│   │   │   │   │   └── sourcemap-codec.umd.js.map
│   │   │   │   ├── LICENSE
│   │   │   │   ├── package.json
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── scopes.ts
│   │   │   │   │   ├── sourcemap-codec.ts
│   │   │   │   │   ├── strings.ts
│   │   │   │   │   └── vlq.ts
│   │   │   │   └── types
│   │   │   │       ├── scopes.d.cts
│   │   │   │       ├── scopes.d.cts.map
│   │   │   │       ├── scopes.d.mts
│   │   │   │       ├── scopes.d.mts.map
│   │   │   │       ├── sourcemap-codec.d.cts
│   │   │   │       ├── sourcemap-codec.d.cts.map
│   │   │   │       ├── sourcemap-codec.d.mts
│   │   │   │       ├── sourcemap-codec.d.mts.map
│   │   │   │       ├── strings.d.cts
│   │   │   │       ├── strings.d.cts.map
│   │   │   │       ├── strings.d.mts
│   │   │   │       ├── strings.d.mts.map
│   │   │   │       ├── vlq.d.cts
│   │   │   │       ├── vlq.d.cts.map
│   │   │   │       ├── vlq.d.mts
│   │   │   │       └── vlq.d.mts.map
│   │   │   └── trace-mapping
│   │   │       ├── dist
│   │   │       │   ├── trace-mapping.mjs
│   │   │       │   ├── trace-mapping.mjs.map
│   │   │       │   ├── trace-mapping.umd.js
│   │   │       │   └── trace-mapping.umd.js.map
│   │   │       ├── LICENSE
│   │   │       ├── package.json
│   │   │       ├── README.md
│   │   │       ├── src
│   │   │       │   ├── binary-search.ts
│   │   │       │   ├── by-source.ts
│   │   │       │   ├── flatten-map.ts
│   │   │       │   ├── resolve.ts
│   │   │       │   ├── sort.ts
│   │   │       │   ├── sourcemap-segment.ts
│   │   │       │   ├── strip-filename.ts
│   │   │       │   ├── trace-mapping.ts
│   │   │       │   └── types.ts
│   │   │       └── types
│   │   │           ├── binary-search.d.cts
│   │   │           ├── binary-search.d.cts.map
│   │   │           ├── binary-search.d.mts
│   │   │           ├── binary-search.d.mts.map
│   │   │           ├── by-source.d.cts
│   │   │           ├── by-source.d.cts.map
│   │   │           ├── by-source.d.mts
│   │   │           ├── by-source.d.mts.map
│   │   │           ├── flatten-map.d.cts
│   │   │           ├── flatten-map.d.cts.map
│   │   │           ├── flatten-map.d.mts
│   │   │           ├── flatten-map.d.mts.map
│   │   │           ├── resolve.d.cts
│   │   │           ├── resolve.d.cts.map
│   │   │           ├── resolve.d.mts
│   │   │           ├── resolve.d.mts.map
│   │   │           ├── sort.d.cts
│   │   │           ├── sort.d.cts.map
│   │   │           ├── sort.d.mts
│   │   │           ├── sort.d.mts.map
│   │   │           ├── sourcemap-segment.d.cts
│   │   │           ├── sourcemap-segment.d.cts.map
│   │   │           ├── sourcemap-segment.d.mts
│   │   │           ├── sourcemap-segment.d.mts.map
│   │   │           ├── strip-filename.d.cts
│   │   │           ├── strip-filename.d.cts.map
│   │   │           ├── strip-filename.d.mts
│   │   │           ├── strip-filename.d.mts.map
│   │   │           ├── trace-mapping.d.cts
│   │   │           ├── trace-mapping.d.cts.map
│   │   │           ├── trace-mapping.d.mts
│   │   │           ├── trace-mapping.d.mts.map
│   │   │           ├── types.d.cts
│   │   │           ├── types.d.cts.map
│   │   │           ├── types.d.mts
│   │   │           └── types.d.mts.map
│   │   ├── @kurkle
│   │   │   └── color
│   │   │       ├── dist
│   │   │       │   ├── color.cjs
│   │   │       │   ├── color.d.ts
│   │   │       │   ├── color.esm.js
│   │   │       │   ├── color.min.js
│   │   │       │   └── color.min.js.map
│   │   │       ├── LICENSE.md
│   │   │       ├── package.json
│   │   │       └── README.md
│   │   ├── leaflet
│   │   │   ├── CHANGELOG.md
│   │   │   ├── dist
│   │   │   │   ├── images
│   │   │   │   │   ├── layers-2x.png
│   │   │   │   │   ├── layers.png
│   │   │   │   │   ├── marker-icon-2x.png
│   │   │   │   │   ├── marker-icon.png
│   │   │   │   │   └── marker-shadow.png
│   │   │   │   ├── leaflet.css
│   │   │   │   ├── leaflet.js
│   │   │   │   ├── leaflet.js.map
│   │   │   │   ├── leaflet-src.esm.js
│   │   │   │   ├── leaflet-src.esm.js.map
│   │   │   │   ├── leaflet-src.js
│   │   │   │   └── leaflet-src.js.map
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── src
│   │   │       ├── control
│   │   │       │   ├── Control.Attribution.js
│   │   │       │   ├── Control.js
│   │   │       │   ├── Control.Layers.js
│   │   │       │   ├── Control.Scale.js
│   │   │       │   ├── Control.Zoom.js
│   │   │       │   └── index.js
│   │   │       ├── core
│   │   │       │   ├── Browser.js
│   │   │       │   ├── Class.js
│   │   │       │   ├── Class.leafdoc
│   │   │       │   ├── Events.js
│   │   │       │   ├── Events.leafdoc
│   │   │       │   ├── Handler.js
│   │   │       │   ├── index.js
│   │   │       │   └── Util.js
│   │   │       ├── dom
│   │   │       │   ├── DomEvent.DoubleTap.js
│   │   │       │   ├── DomEvent.js
│   │   │       │   ├── DomEvent.Pointer.js
│   │   │       │   ├── DomUtil.js
│   │   │       │   ├── Draggable.js
│   │   │       │   ├── index.js
│   │   │       │   └── PosAnimation.js
│   │   │       ├── geo
│   │   │       │   ├── crs
│   │   │       │   │   ├── CRS.Earth.js
│   │   │       │   │   ├── CRS.EPSG3395.js
│   │   │       │   │   ├── CRS.EPSG3857.js
│   │   │       │   │   ├── CRS.EPSG4326.js
│   │   │       │   │   ├── CRS.js
│   │   │       │   │   ├── CRS.Simple.js
│   │   │       │   │   └── index.js
│   │   │       │   ├── index.js
│   │   │       │   ├── LatLngBounds.js
│   │   │       │   ├── LatLng.js
│   │   │       │   └── projection
│   │   │       │       ├── index.js
│   │   │       │       ├── Projection.LonLat.js
│   │   │       │       ├── Projection.Mercator.js
│   │   │       │       └── Projection.SphericalMercator.js
│   │   │       ├── geometry
│   │   │       │   ├── Bounds.js
│   │   │       │   ├── index.js
│   │   │       │   ├── LineUtil.js
│   │   │       │   ├── Point.js
│   │   │       │   ├── PolyUtil.js
│   │   │       │   └── Transformation.js
│   │   │       ├── images
│   │   │       │   ├── layers.svg
│   │   │       │   ├── logo.svg
│   │   │       │   └── marker.svg
│   │   │       ├── layer
│   │   │       │   ├── DivOverlay.js
│   │   │       │   ├── FeatureGroup.js
│   │   │       │   ├── GeoJSON.js
│   │   │       │   ├── ImageOverlay.js
│   │   │       │   ├── index.js
│   │   │       │   ├── LayerGroup.js
│   │   │       │   ├── Layer.Interactive.leafdoc
│   │   │       │   ├── Layer.js
│   │   │       │   ├── marker
│   │   │       │   │   ├── DivIcon.js
│   │   │       │   │   ├── Icon.Default.js
│   │   │       │   │   ├── Icon.js
│   │   │       │   │   ├── index.js
│   │   │       │   │   ├── Marker.Drag.js
│   │   │       │   │   └── Marker.js
│   │   │       │   ├── Popup.js
│   │   │       │   ├── SVGOverlay.js
│   │   │       │   ├── tile
│   │   │       │   │   ├── GridLayer.js
│   │   │       │   │   ├── index.js
│   │   │       │   │   ├── TileLayer.js
│   │   │       │   │   └── TileLayer.WMS.js
│   │   │       │   ├── Tooltip.js
│   │   │       │   ├── vector
│   │   │       │   │   ├── Canvas.js
│   │   │       │   │   ├── Circle.js
│   │   │       │   │   ├── CircleMarker.js
│   │   │       │   │   ├── index.js
│   │   │       │   │   ├── Path.js
│   │   │       │   │   ├── Polygon.js
│   │   │       │   │   ├── Polyline.js
│   │   │       │   │   ├── Rectangle.js
│   │   │       │   │   ├── Renderer.getRenderer.js
│   │   │       │   │   ├── Renderer.js
│   │   │       │   │   ├── SVG.js
│   │   │       │   │   ├── SVG.Util.js
│   │   │       │   │   └── SVG.VML.js
│   │   │       │   └── VideoOverlay.js
│   │   │       ├── Leaflet.js
│   │   │       └── map
│   │   │           ├── handler
│   │   │           │   ├── Map.BoxZoom.js
│   │   │           │   ├── Map.DoubleClickZoom.js
│   │   │           │   ├── Map.Drag.js
│   │   │           │   ├── Map.Keyboard.js
│   │   │           │   ├── Map.ScrollWheelZoom.js
│   │   │           │   ├── Map.TapHold.js
│   │   │           │   └── Map.TouchZoom.js
│   │   │           ├── index.js
│   │   │           ├── Map.js
│   │   │           └── Map.methodOptions.leafdoc
│   │   ├── lilconfig
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── readme.md
│   │   │   └── src
│   │   │       ├── index.d.ts
│   │   │       └── index.js
│   │   ├── lines-and-columns
│   │   │   ├── build
│   │   │   │   ├── index.d.ts
│   │   │   │   └── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── merge2
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── micromatch
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── mz
│   │   │   ├── child_process.js
│   │   │   ├── crypto.js
│   │   │   ├── dns.js
│   │   │   ├── fs.js
│   │   │   ├── HISTORY.md
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── readline.js
│   │   │   ├── README.md
│   │   │   └── zlib.js
│   │   ├── nanoid
│   │   │   ├── async
│   │   │   │   ├── index.browser.cjs
│   │   │   │   ├── index.browser.js
│   │   │   │   ├── index.cjs
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   ├── index.native.js
│   │   │   │   └── package.json
│   │   │   ├── bin
│   │   │   │   └── nanoid.cjs
│   │   │   ├── index.browser.cjs
│   │   │   ├── index.browser.js
│   │   │   ├── index.cjs
│   │   │   ├── index.d.cts
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── nanoid.js
│   │   │   ├── non-secure
│   │   │   │   ├── index.cjs
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   └── package.json
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── url-alphabet
│   │   │       ├── index.cjs
│   │   │       ├── index.js
│   │   │       └── package.json
│   │   ├── @nodelib
│   │   │   ├── fs.scandir
│   │   │   │   ├── LICENSE
│   │   │   │   ├── out
│   │   │   │   │   ├── adapters
│   │   │   │   │   │   ├── fs.d.ts
│   │   │   │   │   │   └── fs.js
│   │   │   │   │   ├── constants.d.ts
│   │   │   │   │   ├── constants.js
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── providers
│   │   │   │   │   │   ├── async.d.ts
│   │   │   │   │   │   ├── async.js
│   │   │   │   │   │   ├── common.d.ts
│   │   │   │   │   │   ├── common.js
│   │   │   │   │   │   ├── sync.d.ts
│   │   │   │   │   │   └── sync.js
│   │   │   │   │   ├── settings.d.ts
│   │   │   │   │   ├── settings.js
│   │   │   │   │   ├── types
│   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   └── index.js
│   │   │   │   │   └── utils
│   │   │   │   │       ├── fs.d.ts
│   │   │   │   │       ├── fs.js
│   │   │   │   │       ├── index.d.ts
│   │   │   │   │       └── index.js
│   │   │   │   ├── package.json
│   │   │   │   └── README.md
│   │   │   ├── fs.stat
│   │   │   │   ├── LICENSE
│   │   │   │   ├── out
│   │   │   │   │   ├── adapters
│   │   │   │   │   │   ├── fs.d.ts
│   │   │   │   │   │   └── fs.js
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── providers
│   │   │   │   │   │   ├── async.d.ts
│   │   │   │   │   │   ├── async.js
│   │   │   │   │   │   ├── sync.d.ts
│   │   │   │   │   │   └── sync.js
│   │   │   │   │   ├── settings.d.ts
│   │   │   │   │   ├── settings.js
│   │   │   │   │   └── types
│   │   │   │   │       ├── index.d.ts
│   │   │   │   │       └── index.js
│   │   │   │   ├── package.json
│   │   │   │   └── README.md
│   │   │   └── fs.walk
│   │   │       ├── LICENSE
│   │   │       ├── out
│   │   │       │   ├── index.d.ts
│   │   │       │   ├── index.js
│   │   │       │   ├── providers
│   │   │       │   │   ├── async.d.ts
│   │   │       │   │   ├── async.js
│   │   │       │   │   ├── index.d.ts
│   │   │       │   │   ├── index.js
│   │   │       │   │   ├── stream.d.ts
│   │   │       │   │   ├── stream.js
│   │   │       │   │   ├── sync.d.ts
│   │   │       │   │   └── sync.js
│   │   │       │   ├── readers
│   │   │       │   │   ├── async.d.ts
│   │   │       │   │   ├── async.js
│   │   │       │   │   ├── common.d.ts
│   │   │       │   │   ├── common.js
│   │   │       │   │   ├── reader.d.ts
│   │   │       │   │   ├── reader.js
│   │   │       │   │   ├── sync.d.ts
│   │   │       │   │   └── sync.js
│   │   │       │   ├── settings.d.ts
│   │   │       │   ├── settings.js
│   │   │       │   └── types
│   │   │       │       ├── index.d.ts
│   │   │       │       └── index.js
│   │   │       ├── package.json
│   │   │       └── README.md
│   │   ├── node-releases
│   │   │   ├── data
│   │   │   │   ├── processed
│   │   │   │   │   └── envs.json
│   │   │   │   └── release-schedule
│   │   │   │       └── release-schedule.json
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── normalize-path
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── object-assign
│   │   │   ├── index.js
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   └── readme.md
│   │   ├── object-hash
│   │   │   ├── dist
│   │   │   │   └── object_hash.js
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── readme.markdown
│   │   ├── path-parse
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── picocolors
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── picocolors.browser.js
│   │   │   ├── picocolors.d.ts
│   │   │   ├── picocolors.js
│   │   │   ├── README.md
│   │   │   └── types.d.ts
│   │   ├── picomatch
│   │   │   ├── index.js
│   │   │   ├── lib
│   │   │   │   ├── constants.js
│   │   │   │   ├── parse.js
│   │   │   │   ├── picomatch.js
│   │   │   │   ├── scan.js
│   │   │   │   └── utils.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── pify
│   │   │   ├── index.js
│   │   │   ├── license
│   │   │   ├── package.json
│   │   │   └── readme.md
│   │   ├── pirates
│   │   │   ├── index.d.ts
│   │   │   ├── lib
│   │   │   │   └── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── postcss
│   │   │   ├── lib
│   │   │   │   ├── at-rule.d.ts
│   │   │   │   ├── at-rule.js
│   │   │   │   ├── comment.d.ts
│   │   │   │   ├── comment.js
│   │   │   │   ├── container.d.ts
│   │   │   │   ├── container.js
│   │   │   │   ├── css-syntax-error.d.ts
│   │   │   │   ├── css-syntax-error.js
│   │   │   │   ├── declaration.d.ts
│   │   │   │   ├── declaration.js
│   │   │   │   ├── document.d.ts
│   │   │   │   ├── document.js
│   │   │   │   ├── fromJSON.d.ts
│   │   │   │   ├── fromJSON.js
│   │   │   │   ├── input.d.ts
│   │   │   │   ├── input.js
│   │   │   │   ├── lazy-result.d.ts
│   │   │   │   ├── lazy-result.js
│   │   │   │   ├── list.d.ts
│   │   │   │   ├── list.js
│   │   │   │   ├── map-generator.js
│   │   │   │   ├── node.d.ts
│   │   │   │   ├── node.js
│   │   │   │   ├── no-work-result.d.ts
│   │   │   │   ├── no-work-result.js
│   │   │   │   ├── parse.d.ts
│   │   │   │   ├── parse.js
│   │   │   │   ├── parser.js
│   │   │   │   ├── postcss.d.mts
│   │   │   │   ├── postcss.d.ts
│   │   │   │   ├── postcss.js
│   │   │   │   ├── postcss.mjs
│   │   │   │   ├── previous-map.d.ts
│   │   │   │   ├── previous-map.js
│   │   │   │   ├── processor.d.ts
│   │   │   │   ├── processor.js
│   │   │   │   ├── result.d.ts
│   │   │   │   ├── result.js
│   │   │   │   ├── root.d.ts
│   │   │   │   ├── root.js
│   │   │   │   ├── rule.d.ts
│   │   │   │   ├── rule.js
│   │   │   │   ├── stringifier.d.ts
│   │   │   │   ├── stringifier.js
│   │   │   │   ├── stringify.d.ts
│   │   │   │   ├── stringify.js
│   │   │   │   ├── symbols.js
│   │   │   │   ├── terminal-highlight.js
│   │   │   │   ├── tokenize.js
│   │   │   │   ├── warning.d.ts
│   │   │   │   ├── warning.js
│   │   │   │   └── warn-once.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── postcss-import
│   │   │   ├── index.js
│   │   │   ├── lib
│   │   │   │   ├── assign-layer-names.js
│   │   │   │   ├── data-url.js
│   │   │   │   ├── join-layer.js
│   │   │   │   ├── join-media.js
│   │   │   │   ├── load-content.js
│   │   │   │   ├── parse-statements.js
│   │   │   │   ├── process-content.js
│   │   │   │   └── resolve-id.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── postcss-js
│   │   │   ├── async.js
│   │   │   ├── index.js
│   │   │   ├── index.mjs
│   │   │   ├── LICENSE
│   │   │   ├── objectifier.js
│   │   │   ├── package.json
│   │   │   ├── parser.js
│   │   │   ├── process-result.js
│   │   │   ├── README.md
│   │   │   └── sync.js
│   │   ├── postcss-load-config
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── src
│   │   │       ├── index.d.ts
│   │   │       ├── index.js
│   │   │       ├── options.js
│   │   │       ├── plugins.js
│   │   │       └── req.js
│   │   ├── postcss-nested
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── postcss-selector-parser
│   │   │   ├── API.md
│   │   │   ├── CHANGELOG.md
│   │   │   ├── dist
│   │   │   │   ├── index.js
│   │   │   │   ├── parser.js
│   │   │   │   ├── processor.js
│   │   │   │   ├── selectors
│   │   │   │   │   ├── attribute.js
│   │   │   │   │   ├── className.js
│   │   │   │   │   ├── combinator.js
│   │   │   │   │   ├── comment.js
│   │   │   │   │   ├── constructors.js
│   │   │   │   │   ├── container.js
│   │   │   │   │   ├── guards.js
│   │   │   │   │   ├── id.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── namespace.js
│   │   │   │   │   ├── nesting.js
│   │   │   │   │   ├── node.js
│   │   │   │   │   ├── pseudo.js
│   │   │   │   │   ├── root.js
│   │   │   │   │   ├── selector.js
│   │   │   │   │   ├── string.js
│   │   │   │   │   ├── tag.js
│   │   │   │   │   ├── types.js
│   │   │   │   │   └── universal.js
│   │   │   │   ├── sortAscending.js
│   │   │   │   ├── tokenize.js
│   │   │   │   ├── tokenTypes.js
│   │   │   │   └── util
│   │   │   │       ├── ensureObject.js
│   │   │   │       ├── getProp.js
│   │   │   │       ├── index.js
│   │   │   │       ├── stripComments.js
│   │   │   │       └── unesc.js
│   │   │   ├── LICENSE-MIT
│   │   │   ├── package.json
│   │   │   ├── postcss-selector-parser.d.ts
│   │   │   └── README.md
│   │   ├── postcss-value-parser
│   │   │   ├── lib
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   ├── parse.js
│   │   │   │   ├── stringify.js
│   │   │   │   ├── unit.js
│   │   │   │   └── walk.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── queue-microtask
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── read-cache
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── readdirp
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── resolve
│   │   │   ├── async.js
│   │   │   ├── bin
│   │   │   │   └── resolve
│   │   │   ├── eslint.config.mjs
│   │   │   ├── example
│   │   │   │   ├── async.js
│   │   │   │   └── sync.js
│   │   │   ├── index.js
│   │   │   ├── lib
│   │   │   │   ├── async.js
│   │   │   │   ├── caller.js
│   │   │   │   ├── core.js
│   │   │   │   ├── core.json
│   │   │   │   ├── homedir.js
│   │   │   │   ├── is-core.js
│   │   │   │   ├── node-modules-paths.js
│   │   │   │   ├── normalize-options.js
│   │   │   │   └── sync.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── readme.markdown
│   │   │   ├── SECURITY.md
│   │   │   ├── sync.js
│   │   │   └── test
│   │   │       ├── core.js
│   │   │       ├── default_paths.js
│   │   │       ├── dotdot
│   │   │       │   ├── abc
│   │   │       │   │   └── index.js
│   │   │       │   └── index.js
│   │   │       ├── dotdot.js
│   │   │       ├── faulty_basedir.js
│   │   │       ├── filter.js
│   │   │       ├── filter_sync.js
│   │   │       ├── homedir.js
│   │   │       ├── home_paths.js
│   │   │       ├── home_paths_sync.js
│   │   │       ├── mock.js
│   │   │       ├── mock_sync.js
│   │   │       ├── module_dir
│   │   │       │   ├── xmodules
│   │   │       │   │   └── aaa
│   │   │       │   │       └── index.js
│   │   │       │   ├── ymodules
│   │   │       │   │   └── aaa
│   │   │       │   │       └── index.js
│   │   │       │   └── zmodules
│   │   │       │       └── bbb
│   │   │       │           ├── main.js
│   │   │       │           └── package.json
│   │   │       ├── module_dir.js
│   │   │       ├── node-modules-paths.js
│   │   │       ├── node_path
│   │   │       │   ├── x
│   │   │       │   │   ├── aaa
│   │   │       │   │   │   └── index.js
│   │   │       │   │   └── ccc
│   │   │       │   │       └── index.js
│   │   │       │   └── y
│   │   │       │       ├── bbb
│   │   │       │       │   └── index.js
│   │   │       │       └── ccc
│   │   │       │           └── index.js
│   │   │       ├── node_path.js
│   │   │       ├── nonstring.js
│   │   │       ├── pathfilter
│   │   │       │   └── deep_ref
│   │   │       │       └── main.js
│   │   │       ├── pathfilter.js
│   │   │       ├── pathfilter_sync.js
│   │   │       ├── precedence
│   │   │       │   ├── aaa
│   │   │       │   │   ├── index.js
│   │   │       │   │   └── main.js
│   │   │       │   ├── aaa.js
│   │   │       │   ├── bbb
│   │   │       │   │   └── main.js
│   │   │       │   └── bbb.js
│   │   │       ├── precedence.js
│   │   │       ├── resolver
│   │   │       │   ├── baz
│   │   │       │   │   ├── doom.js
│   │   │       │   │   ├── package.json
│   │   │       │   │   └── quux.js
│   │   │       │   ├── browser_field
│   │   │       │   │   ├── a.js
│   │   │       │   │   ├── b.js
│   │   │       │   │   └── package.json
│   │   │       │   ├── cup.coffee
│   │   │       │   ├── dot_main
│   │   │       │   │   ├── index.js
│   │   │       │   │   └── package.json
│   │   │       │   ├── dot_slash_main
│   │   │       │   │   ├── index.js
│   │   │       │   │   └── package.json
│   │   │       │   ├── false_main
│   │   │       │   │   ├── index.js
│   │   │       │   │   └── package.json
│   │   │       │   ├── foo.js
│   │   │       │   ├── incorrect_main
│   │   │       │   │   ├── index.js
│   │   │       │   │   └── package.json
│   │   │       │   ├── invalid_main
│   │   │       │   │   └── package.json
│   │   │       │   ├── mug.coffee
│   │   │       │   ├── mug.js
│   │   │       │   ├── multirepo
│   │   │       │   │   ├── lerna.json
│   │   │       │   │   ├── package.json
│   │   │       │   │   └── packages
│   │   │       │   │       ├── package-a
│   │   │       │   │       │   ├── index.js
│   │   │       │   │       │   └── package.json
│   │   │       │   │       └── package-b
│   │   │       │   │           ├── index.js
│   │   │       │   │           └── package.json
│   │   │       │   ├── nested_symlinks
│   │   │       │   │   └── mylib
│   │   │       │   │       ├── async.js
│   │   │       │   │       ├── package.json
│   │   │       │   │       └── sync.js
│   │   │       │   ├── other_path
│   │   │       │   │   ├── lib
│   │   │       │   │   │   └── other-lib.js
│   │   │       │   │   └── root.js
│   │   │       │   ├── quux
│   │   │       │   │   └── foo
│   │   │       │   │       └── index.js
│   │   │       │   ├── same_names
│   │   │       │   │   ├── foo
│   │   │       │   │   │   └── index.js
│   │   │       │   │   └── foo.js
│   │   │       │   ├── symlinked
│   │   │       │   │   ├── _
│   │   │       │   │   │   ├── node_modules
│   │   │       │   │   │   │   └── foo.js
│   │   │       │   │   │   └── symlink_target
│   │   │       │   │   └── package
│   │   │       │   │       ├── bar.js
│   │   │       │   │       └── package.json
│   │   │       │   └── without_basedir
│   │   │       │       └── main.js
│   │   │       ├── resolver.js
│   │   │       ├── resolver_sync.js
│   │   │       ├── shadowed_core
│   │   │       │   └── node_modules
│   │   │       │       └── util
│   │   │       │           └── index.js
│   │   │       ├── shadowed_core.js
│   │   │       ├── subdirs.js
│   │   │       └── symlinks.js
│   │   ├── reusify
│   │   │   ├── benchmarks
│   │   │   │   ├── createNoCodeFunction.js
│   │   │   │   ├── fib.js
│   │   │   │   └── reuseNoCodeFunction.js
│   │   │   ├── eslint.config.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── reusify.d.ts
│   │   │   ├── reusify.js
│   │   │   ├── SECURITY.md
│   │   │   ├── test.js
│   │   │   └── tsconfig.json
│   │   ├── @rollup
│   │   │   ├── rollup-linux-x64-gnu
│   │   │   │   ├── package.json
│   │   │   │   ├── README.md
│   │   │   │   └── rollup.linux-x64-gnu.node
│   │   │   └── rollup-linux-x64-musl
│   │   │       ├── package.json
│   │   │       ├── README.md
│   │   │       └── rollup.linux-x64-musl.node
│   │   ├── rollup
│   │   │   ├── dist
│   │   │   │   ├── bin
│   │   │   │   │   └── rollup
│   │   │   │   ├── es
│   │   │   │   │   ├── getLogFilter.js
│   │   │   │   │   ├── package.json
│   │   │   │   │   ├── parseAst.js
│   │   │   │   │   ├── rollup.js
│   │   │   │   │   └── shared
│   │   │   │   │       ├── node-entry.js
│   │   │   │   │       ├── parseAst.js
│   │   │   │   │       └── watch.js
│   │   │   │   ├── getLogFilter.d.ts
│   │   │   │   ├── getLogFilter.js
│   │   │   │   ├── loadConfigFile.d.ts
│   │   │   │   ├── loadConfigFile.js
│   │   │   │   ├── native.js
│   │   │   │   ├── parseAst.d.ts
│   │   │   │   ├── parseAst.js
│   │   │   │   ├── rollup.d.ts
│   │   │   │   ├── rollup.js
│   │   │   │   └── shared
│   │   │   │       ├── fsevents-importer.js
│   │   │   │       ├── index.js
│   │   │   │       ├── loadConfigFile.js
│   │   │   │       ├── parseAst.js
│   │   │   │       ├── rollup.js
│   │   │   │       ├── watch-cli.js
│   │   │   │       └── watch.js
│   │   │   ├── LICENSE.md
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── run-parallel
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── source-map-js
│   │   │   ├── lib
│   │   │   │   ├── array-set.js
│   │   │   │   ├── base64.js
│   │   │   │   ├── base64-vlq.js
│   │   │   │   ├── binary-search.js
│   │   │   │   ├── mapping-list.js
│   │   │   │   ├── quick-sort.js
│   │   │   │   ├── source-map-consumer.d.ts
│   │   │   │   ├── source-map-consumer.js
│   │   │   │   ├── source-map-generator.d.ts
│   │   │   │   ├── source-map-generator.js
│   │   │   │   ├── source-node.d.ts
│   │   │   │   ├── source-node.js
│   │   │   │   └── util.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── source-map.d.ts
│   │   │   └── source-map.js
│   │   ├── sucrase
│   │   │   ├── bin
│   │   │   │   ├── sucrase
│   │   │   │   └── sucrase-node
│   │   │   ├── dist
│   │   │   │   ├── CJSImportProcessor.js
│   │   │   │   ├── cli.js
│   │   │   │   ├── computeSourceMap.js
│   │   │   │   ├── esm
│   │   │   │   │   ├── CJSImportProcessor.js
│   │   │   │   │   ├── cli.js
│   │   │   │   │   ├── computeSourceMap.js
│   │   │   │   │   ├── HelperManager.js
│   │   │   │   │   ├── identifyShadowedGlobals.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── NameManager.js
│   │   │   │   │   ├── Options-gen-types.js
│   │   │   │   │   ├── Options.js
│   │   │   │   │   ├── parser
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── plugins
│   │   │   │   │   │   │   ├── flow.js
│   │   │   │   │   │   │   ├── jsx
│   │   │   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   │   │   └── xhtml.js
│   │   │   │   │   │   │   ├── typescript.js
│   │   │   │   │   │   │   └── types.js
│   │   │   │   │   │   ├── tokenizer
│   │   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   │   ├── keywords.js
│   │   │   │   │   │   │   ├── readWord.js
│   │   │   │   │   │   │   ├── readWordTree.js
│   │   │   │   │   │   │   ├── state.js
│   │   │   │   │   │   │   └── types.js
│   │   │   │   │   │   ├── traverser
│   │   │   │   │   │   │   ├── base.js
│   │   │   │   │   │   │   ├── expression.js
│   │   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   │   ├── lval.js
│   │   │   │   │   │   │   ├── statement.js
│   │   │   │   │   │   │   └── util.js
│   │   │   │   │   │   └── util
│   │   │   │   │   │       ├── charcodes.js
│   │   │   │   │   │       ├── identifier.js
│   │   │   │   │   │       └── whitespace.js
│   │   │   │   │   ├── register.js
│   │   │   │   │   ├── TokenProcessor.js
│   │   │   │   │   ├── transformers
│   │   │   │   │   │   ├── CJSImportTransformer.js
│   │   │   │   │   │   ├── ESMImportTransformer.js
│   │   │   │   │   │   ├── FlowTransformer.js
│   │   │   │   │   │   ├── JestHoistTransformer.js
│   │   │   │   │   │   ├── JSXTransformer.js
│   │   │   │   │   │   ├── NumericSeparatorTransformer.js
│   │   │   │   │   │   ├── OptionalCatchBindingTransformer.js
│   │   │   │   │   │   ├── OptionalChainingNullishTransformer.js
│   │   │   │   │   │   ├── ReactDisplayNameTransformer.js
│   │   │   │   │   │   ├── ReactHotLoaderTransformer.js
│   │   │   │   │   │   ├── RootTransformer.js
│   │   │   │   │   │   ├── Transformer.js
│   │   │   │   │   │   └── TypeScriptTransformer.js
│   │   │   │   │   └── util
│   │   │   │   │       ├── elideImportEquals.js
│   │   │   │   │       ├── formatTokens.js
│   │   │   │   │       ├── getClassInfo.js
│   │   │   │   │       ├── getDeclarationInfo.js
│   │   │   │   │       ├── getIdentifierNames.js
│   │   │   │   │       ├── getImportExportSpecifierInfo.js
│   │   │   │   │       ├── getJSXPragmaInfo.js
│   │   │   │   │       ├── getNonTypeIdentifiers.js
│   │   │   │   │       ├── getTSImportedNames.js
│   │   │   │   │       ├── isAsyncOperation.js
│   │   │   │   │       ├── isExportFrom.js
│   │   │   │   │       ├── isIdentifier.js
│   │   │   │   │       ├── removeMaybeImportAttributes.js
│   │   │   │   │       └── shouldElideDefaultExport.js
│   │   │   │   ├── HelperManager.js
│   │   │   │   ├── identifyShadowedGlobals.js
│   │   │   │   ├── index.js
│   │   │   │   ├── NameManager.js
│   │   │   │   ├── Options-gen-types.js
│   │   │   │   ├── Options.js
│   │   │   │   ├── parser
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── plugins
│   │   │   │   │   │   ├── flow.js
│   │   │   │   │   │   ├── jsx
│   │   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   │   └── xhtml.js
│   │   │   │   │   │   ├── typescript.js
│   │   │   │   │   │   └── types.js
│   │   │   │   │   ├── tokenizer
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── keywords.js
│   │   │   │   │   │   ├── readWord.js
│   │   │   │   │   │   ├── readWordTree.js
│   │   │   │   │   │   ├── state.js
│   │   │   │   │   │   └── types.js
│   │   │   │   │   ├── traverser
│   │   │   │   │   │   ├── base.js
│   │   │   │   │   │   ├── expression.js
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── lval.js
│   │   │   │   │   │   ├── statement.js
│   │   │   │   │   │   └── util.js
│   │   │   │   │   └── util
│   │   │   │   │       ├── charcodes.js
│   │   │   │   │       ├── identifier.js
│   │   │   │   │       └── whitespace.js
│   │   │   │   ├── register.js
│   │   │   │   ├── TokenProcessor.js
│   │   │   │   ├── transformers
│   │   │   │   │   ├── CJSImportTransformer.js
│   │   │   │   │   ├── ESMImportTransformer.js
│   │   │   │   │   ├── FlowTransformer.js
│   │   │   │   │   ├── JestHoistTransformer.js
│   │   │   │   │   ├── JSXTransformer.js
│   │   │   │   │   ├── NumericSeparatorTransformer.js
│   │   │   │   │   ├── OptionalCatchBindingTransformer.js
│   │   │   │   │   ├── OptionalChainingNullishTransformer.js
│   │   │   │   │   ├── ReactDisplayNameTransformer.js
│   │   │   │   │   ├── ReactHotLoaderTransformer.js
│   │   │   │   │   ├── RootTransformer.js
│   │   │   │   │   ├── Transformer.js
│   │   │   │   │   └── TypeScriptTransformer.js
│   │   │   │   ├── types
│   │   │   │   │   ├── CJSImportProcessor.d.ts
│   │   │   │   │   ├── cli.d.ts
│   │   │   │   │   ├── computeSourceMap.d.ts
│   │   │   │   │   ├── HelperManager.d.ts
│   │   │   │   │   ├── identifyShadowedGlobals.d.ts
│   │   │   │   │   ├── index.d.ts
│   │   │   │   │   ├── NameManager.d.ts
│   │   │   │   │   ├── Options.d.ts
│   │   │   │   │   ├── Options-gen-types.d.ts
│   │   │   │   │   ├── parser
│   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   ├── plugins
│   │   │   │   │   │   │   ├── flow.d.ts
│   │   │   │   │   │   │   ├── jsx
│   │   │   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   │   │   └── xhtml.d.ts
│   │   │   │   │   │   │   ├── typescript.d.ts
│   │   │   │   │   │   │   └── types.d.ts
│   │   │   │   │   │   ├── tokenizer
│   │   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   │   ├── keywords.d.ts
│   │   │   │   │   │   │   ├── readWord.d.ts
│   │   │   │   │   │   │   ├── readWordTree.d.ts
│   │   │   │   │   │   │   ├── state.d.ts
│   │   │   │   │   │   │   └── types.d.ts
│   │   │   │   │   │   ├── traverser
│   │   │   │   │   │   │   ├── base.d.ts
│   │   │   │   │   │   │   ├── expression.d.ts
│   │   │   │   │   │   │   ├── index.d.ts
│   │   │   │   │   │   │   ├── lval.d.ts
│   │   │   │   │   │   │   ├── statement.d.ts
│   │   │   │   │   │   │   └── util.d.ts
│   │   │   │   │   │   └── util
│   │   │   │   │   │       ├── charcodes.d.ts
│   │   │   │   │   │       ├── identifier.d.ts
│   │   │   │   │   │       └── whitespace.d.ts
│   │   │   │   │   ├── register.d.ts
│   │   │   │   │   ├── TokenProcessor.d.ts
│   │   │   │   │   ├── transformers
│   │   │   │   │   │   ├── CJSImportTransformer.d.ts
│   │   │   │   │   │   ├── ESMImportTransformer.d.ts
│   │   │   │   │   │   ├── FlowTransformer.d.ts
│   │   │   │   │   │   ├── JestHoistTransformer.d.ts
│   │   │   │   │   │   ├── JSXTransformer.d.ts
│   │   │   │   │   │   ├── NumericSeparatorTransformer.d.ts
│   │   │   │   │   │   ├── OptionalCatchBindingTransformer.d.ts
│   │   │   │   │   │   ├── OptionalChainingNullishTransformer.d.ts
│   │   │   │   │   │   ├── ReactDisplayNameTransformer.d.ts
│   │   │   │   │   │   ├── ReactHotLoaderTransformer.d.ts
│   │   │   │   │   │   ├── RootTransformer.d.ts
│   │   │   │   │   │   ├── Transformer.d.ts
│   │   │   │   │   │   └── TypeScriptTransformer.d.ts
│   │   │   │   │   └── util
│   │   │   │   │       ├── elideImportEquals.d.ts
│   │   │   │   │       ├── formatTokens.d.ts
│   │   │   │   │       ├── getClassInfo.d.ts
│   │   │   │   │       ├── getDeclarationInfo.d.ts
│   │   │   │   │       ├── getIdentifierNames.d.ts
│   │   │   │   │       ├── getImportExportSpecifierInfo.d.ts
│   │   │   │   │       ├── getJSXPragmaInfo.d.ts
│   │   │   │   │       ├── getNonTypeIdentifiers.d.ts
│   │   │   │   │       ├── getTSImportedNames.d.ts
│   │   │   │   │       ├── isAsyncOperation.d.ts
│   │   │   │   │       ├── isExportFrom.d.ts
│   │   │   │   │       ├── isIdentifier.d.ts
│   │   │   │   │       ├── removeMaybeImportAttributes.d.ts
│   │   │   │   │       └── shouldElideDefaultExport.d.ts
│   │   │   │   └── util
│   │   │   │       ├── elideImportEquals.js
│   │   │   │       ├── formatTokens.js
│   │   │   │       ├── getClassInfo.js
│   │   │   │       ├── getDeclarationInfo.js
│   │   │   │       ├── getIdentifierNames.js
│   │   │   │       ├── getImportExportSpecifierInfo.js
│   │   │   │       ├── getJSXPragmaInfo.js
│   │   │   │       ├── getNonTypeIdentifiers.js
│   │   │   │       ├── getTSImportedNames.js
│   │   │   │       ├── isAsyncOperation.js
│   │   │   │       ├── isExportFrom.js
│   │   │   │       ├── isIdentifier.js
│   │   │   │       ├── removeMaybeImportAttributes.js
│   │   │   │       └── shouldElideDefaultExport.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── register
│   │   │   │   ├── index.js
│   │   │   │   ├── js.js
│   │   │   │   ├── jsx.js
│   │   │   │   ├── ts.js
│   │   │   │   ├── ts-legacy-module-interop.js
│   │   │   │   ├── tsx.js
│   │   │   │   └── tsx-legacy-module-interop.js
│   │   │   └── ts-node-plugin
│   │   │       └── index.js
│   │   ├── supports-preserve-symlinks-flag
│   │   │   ├── browser.js
│   │   │   ├── CHANGELOG.md
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── test
│   │   │       └── index.js
│   │   ├── tailwindcss
│   │   │   ├── base.css
│   │   │   ├── colors.d.ts
│   │   │   ├── colors.js
│   │   │   ├── components.css
│   │   │   ├── defaultConfig.d.ts
│   │   │   ├── defaultConfig.js
│   │   │   ├── defaultTheme.d.ts
│   │   │   ├── defaultTheme.js
│   │   │   ├── lib
│   │   │   │   ├── cli
│   │   │   │   │   ├── build
│   │   │   │   │   │   ├── deps.js
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── plugin.js
│   │   │   │   │   │   ├── utils.js
│   │   │   │   │   │   └── watching.js
│   │   │   │   │   ├── help
│   │   │   │   │   │   └── index.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   └── init
│   │   │   │   │       └── index.js
│   │   │   │   ├── cli.js
│   │   │   │   ├── cli-peer-dependencies.js
│   │   │   │   ├── corePluginList.js
│   │   │   │   ├── corePlugins.js
│   │   │   │   ├── css
│   │   │   │   │   ├── LICENSE
│   │   │   │   │   └── preflight.css
│   │   │   │   ├── featureFlags.js
│   │   │   │   ├── index.js
│   │   │   │   ├── lib
│   │   │   │   │   ├── cacheInvalidation.js
│   │   │   │   │   ├── collapseAdjacentRules.js
│   │   │   │   │   ├── collapseDuplicateDeclarations.js
│   │   │   │   │   ├── content.js
│   │   │   │   │   ├── defaultExtractor.js
│   │   │   │   │   ├── evaluateTailwindFunctions.js
│   │   │   │   │   ├── expandApplyAtRules.js
│   │   │   │   │   ├── expandTailwindAtRules.js
│   │   │   │   │   ├── findAtConfigPath.js
│   │   │   │   │   ├── generateRules.js
│   │   │   │   │   ├── getModuleDependencies.js
│   │   │   │   │   ├── load-config.js
│   │   │   │   │   ├── normalizeTailwindDirectives.js
│   │   │   │   │   ├── offsets.js
│   │   │   │   │   ├── partitionApplyAtRules.js
│   │   │   │   │   ├── regex.js
│   │   │   │   │   ├── remap-bitfield.js
│   │   │   │   │   ├── resolveDefaultsAtRules.js
│   │   │   │   │   ├── setupContextUtils.js
│   │   │   │   │   ├── setupTrackingContext.js
│   │   │   │   │   ├── sharedState.js
│   │   │   │   │   └── substituteScreenAtRules.js
│   │   │   │   ├── plugin.js
│   │   │   │   ├── postcss-plugins
│   │   │   │   │   └── nesting
│   │   │   │   │       ├── index.js
│   │   │   │   │       ├── plugin.js
│   │   │   │   │       └── README.md
│   │   │   │   ├── processTailwindFeatures.js
│   │   │   │   ├── public
│   │   │   │   │   ├── colors.js
│   │   │   │   │   ├── create-plugin.js
│   │   │   │   │   ├── default-config.js
│   │   │   │   │   ├── default-theme.js
│   │   │   │   │   ├── load-config.js
│   │   │   │   │   └── resolve-config.js
│   │   │   │   ├── util
│   │   │   │   │   ├── applyImportantSelector.js
│   │   │   │   │   ├── bigSign.js
│   │   │   │   │   ├── buildMediaQuery.js
│   │   │   │   │   ├── cloneDeep.js
│   │   │   │   │   ├── cloneNodes.js
│   │   │   │   │   ├── color.js
│   │   │   │   │   ├── colorNames.js
│   │   │   │   │   ├── configurePlugins.js
│   │   │   │   │   ├── createPlugin.js
│   │   │   │   │   ├── createUtilityPlugin.js
│   │   │   │   │   ├── dataTypes.js
│   │   │   │   │   ├── defaults.js
│   │   │   │   │   ├── escapeClassName.js
│   │   │   │   │   ├── escapeCommas.js
│   │   │   │   │   ├── flattenColorPalette.js
│   │   │   │   │   ├── formatVariantSelector.js
│   │   │   │   │   ├── getAllConfigs.js
│   │   │   │   │   ├── hashConfig.js
│   │   │   │   │   ├── isKeyframeRule.js
│   │   │   │   │   ├── isPlainObject.js
│   │   │   │   │   ├── isSyntacticallyValidPropertyValue.js
│   │   │   │   │   ├── log.js
│   │   │   │   │   ├── math-operators.js
│   │   │   │   │   ├── nameClass.js
│   │   │   │   │   ├── negateValue.js
│   │   │   │   │   ├── normalizeConfig.js
│   │   │   │   │   ├── normalizeScreens.js
│   │   │   │   │   ├── parseAnimationValue.js
│   │   │   │   │   ├── parseBoxShadowValue.js
│   │   │   │   │   ├── parseDependency.js
│   │   │   │   │   ├── parseGlob.js
│   │   │   │   │   ├── parseObjectStyles.js
│   │   │   │   │   ├── pluginUtils.js
│   │   │   │   │   ├── prefixSelector.js
│   │   │   │   │   ├── pseudoElements.js
│   │   │   │   │   ├── removeAlphaVariables.js
│   │   │   │   │   ├── resolveConfig.js
│   │   │   │   │   ├── resolveConfigPath.js
│   │   │   │   │   ├── responsive.js
│   │   │   │   │   ├── splitAtTopLevelOnly.js
│   │   │   │   │   ├── tap.js
│   │   │   │   │   ├── toColorValue.js
│   │   │   │   │   ├── toPath.js
│   │   │   │   │   ├── transformThemeValue.js
│   │   │   │   │   ├── validateConfig.js
│   │   │   │   │   ├── validateFormalSyntax.js
│   │   │   │   │   └── withAlphaVariable.js
│   │   │   │   └── value-parser
│   │   │   │       ├── index.d.js
│   │   │   │       ├── index.js
│   │   │   │       ├── LICENSE
│   │   │   │       ├── parse.js
│   │   │   │       ├── README.md
│   │   │   │       ├── stringify.js
│   │   │   │       ├── unit.js
│   │   │   │       └── walk.js
│   │   │   ├── LICENSE
│   │   │   ├── loadConfig.d.ts
│   │   │   ├── loadConfig.js
│   │   │   ├── nesting
│   │   │   │   ├── index.d.ts
│   │   │   │   └── index.js
│   │   │   ├── package.json
│   │   │   ├── peers
│   │   │   │   └── index.js
│   │   │   ├── plugin.d.ts
│   │   │   ├── plugin.js
│   │   │   ├── prettier.config.js
│   │   │   ├── README.md
│   │   │   ├── resolveConfig.d.ts
│   │   │   ├── resolveConfig.js
│   │   │   ├── screens.css
│   │   │   ├── scripts
│   │   │   │   ├── create-plugin-list.js
│   │   │   │   ├── generate-types.js
│   │   │   │   ├── release-channel.js
│   │   │   │   ├── release-notes.js
│   │   │   │   └── type-utils.js
│   │   │   ├── src
│   │   │   │   ├── cli
│   │   │   │   │   ├── build
│   │   │   │   │   │   ├── deps.js
│   │   │   │   │   │   ├── index.js
│   │   │   │   │   │   ├── plugin.js
│   │   │   │   │   │   ├── utils.js
│   │   │   │   │   │   └── watching.js
│   │   │   │   │   ├── help
│   │   │   │   │   │   └── index.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   └── init
│   │   │   │   │       └── index.js
│   │   │   │   ├── cli.js
│   │   │   │   ├── cli-peer-dependencies.js
│   │   │   │   ├── corePluginList.js
│   │   │   │   ├── corePlugins.js
│   │   │   │   ├── css
│   │   │   │   │   ├── LICENSE
│   │   │   │   │   └── preflight.css
│   │   │   │   ├── featureFlags.js
│   │   │   │   ├── index.js
│   │   │   │   ├── lib
│   │   │   │   │   ├── cacheInvalidation.js
│   │   │   │   │   ├── collapseAdjacentRules.js
│   │   │   │   │   ├── collapseDuplicateDeclarations.js
│   │   │   │   │   ├── content.js
│   │   │   │   │   ├── defaultExtractor.js
│   │   │   │   │   ├── evaluateTailwindFunctions.js
│   │   │   │   │   ├── expandApplyAtRules.js
│   │   │   │   │   ├── expandTailwindAtRules.js
│   │   │   │   │   ├── findAtConfigPath.js
│   │   │   │   │   ├── generateRules.js
│   │   │   │   │   ├── getModuleDependencies.js
│   │   │   │   │   ├── load-config.ts
│   │   │   │   │   ├── normalizeTailwindDirectives.js
│   │   │   │   │   ├── offsets.js
│   │   │   │   │   ├── partitionApplyAtRules.js
│   │   │   │   │   ├── regex.js
│   │   │   │   │   ├── remap-bitfield.js
│   │   │   │   │   ├── resolveDefaultsAtRules.js
│   │   │   │   │   ├── setupContextUtils.js
│   │   │   │   │   ├── setupTrackingContext.js
│   │   │   │   │   ├── sharedState.js
│   │   │   │   │   └── substituteScreenAtRules.js
│   │   │   │   ├── plugin.js
│   │   │   │   ├── postcss-plugins
│   │   │   │   │   └── nesting
│   │   │   │   │       ├── index.js
│   │   │   │   │       ├── plugin.js
│   │   │   │   │       └── README.md
│   │   │   │   ├── processTailwindFeatures.js
│   │   │   │   ├── public
│   │   │   │   │   ├── colors.js
│   │   │   │   │   ├── create-plugin.js
│   │   │   │   │   ├── default-config.js
│   │   │   │   │   ├── default-theme.js
│   │   │   │   │   ├── load-config.js
│   │   │   │   │   └── resolve-config.js
│   │   │   │   ├── util
│   │   │   │   │   ├── applyImportantSelector.js
│   │   │   │   │   ├── bigSign.js
│   │   │   │   │   ├── buildMediaQuery.js
│   │   │   │   │   ├── cloneDeep.js
│   │   │   │   │   ├── cloneNodes.js
│   │   │   │   │   ├── color.js
│   │   │   │   │   ├── colorNames.js
│   │   │   │   │   ├── configurePlugins.js
│   │   │   │   │   ├── createPlugin.js
│   │   │   │   │   ├── createUtilityPlugin.js
│   │   │   │   │   ├── dataTypes.js
│   │   │   │   │   ├── defaults.js
│   │   │   │   │   ├── escapeClassName.js
│   │   │   │   │   ├── escapeCommas.js
│   │   │   │   │   ├── flattenColorPalette.js
│   │   │   │   │   ├── formatVariantSelector.js
│   │   │   │   │   ├── getAllConfigs.js
│   │   │   │   │   ├── hashConfig.js
│   │   │   │   │   ├── isKeyframeRule.js
│   │   │   │   │   ├── isPlainObject.js
│   │   │   │   │   ├── isSyntacticallyValidPropertyValue.js
│   │   │   │   │   ├── log.js
│   │   │   │   │   ├── math-operators.ts
│   │   │   │   │   ├── nameClass.js
│   │   │   │   │   ├── negateValue.js
│   │   │   │   │   ├── normalizeConfig.js
│   │   │   │   │   ├── normalizeScreens.js
│   │   │   │   │   ├── parseAnimationValue.js
│   │   │   │   │   ├── parseBoxShadowValue.js
│   │   │   │   │   ├── parseDependency.js
│   │   │   │   │   ├── parseGlob.js
│   │   │   │   │   ├── parseObjectStyles.js
│   │   │   │   │   ├── pluginUtils.js
│   │   │   │   │   ├── prefixSelector.js
│   │   │   │   │   ├── pseudoElements.js
│   │   │   │   │   ├── removeAlphaVariables.js
│   │   │   │   │   ├── resolveConfig.js
│   │   │   │   │   ├── resolveConfigPath.js
│   │   │   │   │   ├── responsive.js
│   │   │   │   │   ├── splitAtTopLevelOnly.js
│   │   │   │   │   ├── tap.js
│   │   │   │   │   ├── toColorValue.js
│   │   │   │   │   ├── toPath.js
│   │   │   │   │   ├── transformThemeValue.js
│   │   │   │   │   ├── validateConfig.js
│   │   │   │   │   ├── validateFormalSyntax.js
│   │   │   │   │   └── withAlphaVariable.js
│   │   │   │   └── value-parser
│   │   │   │       ├── index.d.ts
│   │   │   │       ├── index.js
│   │   │   │       ├── LICENSE
│   │   │   │       ├── parse.js
│   │   │   │       ├── README.md
│   │   │   │       ├── stringify.js
│   │   │   │       ├── unit.js
│   │   │   │       └── walk.js
│   │   │   ├── stubs
│   │   │   │   ├── config.full.js
│   │   │   │   ├── config.simple.js
│   │   │   │   ├── postcss.config.cjs
│   │   │   │   ├── postcss.config.js
│   │   │   │   ├── tailwind.config.cjs
│   │   │   │   ├── tailwind.config.js
│   │   │   │   └── tailwind.config.ts
│   │   │   ├── tailwind.css
│   │   │   ├── types
│   │   │   │   ├── config.d.ts
│   │   │   │   ├── generated
│   │   │   │   │   ├── colors.d.ts
│   │   │   │   │   ├── corePluginList.d.ts
│   │   │   │   │   └── default-theme.d.ts
│   │   │   │   └── index.d.ts
│   │   │   ├── utilities.css
│   │   │   └── variants.css
│   │   ├── thenify
│   │   │   ├── History.md
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── thenify-all
│   │   │   ├── History.md
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── tinyglobby
│   │   │   ├── dist
│   │   │   │   ├── index.cjs
│   │   │   │   ├── index.d.cts
│   │   │   │   ├── index.d.mts
│   │   │   │   └── index.mjs
│   │   │   ├── LICENSE
│   │   │   ├── node_modules
│   │   │   │   ├── fdir
│   │   │   │   │   ├── dist
│   │   │   │   │   │   ├── index.cjs
│   │   │   │   │   │   ├── index.d.cts
│   │   │   │   │   │   ├── index.d.mts
│   │   │   │   │   │   └── index.mjs
│   │   │   │   │   ├── LICENSE
│   │   │   │   │   ├── package.json
│   │   │   │   │   └── README.md
│   │   │   │   └── picomatch
│   │   │   │       ├── index.js
│   │   │   │       ├── lib
│   │   │   │       │   ├── constants.js
│   │   │   │       │   ├── parse.js
│   │   │   │       │   ├── picomatch.js
│   │   │   │       │   ├── scan.js
│   │   │   │       │   └── utils.js
│   │   │   │       ├── LICENSE
│   │   │   │       ├── package.json
│   │   │   │       ├── posix.js
│   │   │   │       └── README.md
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── to-regex-range
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── ts-interface-checker
│   │   │   ├── dist
│   │   │   │   ├── index.d.ts
│   │   │   │   ├── index.js
│   │   │   │   ├── types.d.ts
│   │   │   │   ├── types.js
│   │   │   │   ├── util.d.ts
│   │   │   │   └── util.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── @types
│   │   │   └── estree
│   │   │       ├── flow.d.ts
│   │   │       ├── index.d.ts
│   │   │       ├── LICENSE
│   │   │       ├── package.json
│   │   │       └── README.md
│   │   ├── update-browserslist-db
│   │   │   ├── check-npm-version.js
│   │   │   ├── cli.js
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── utils.js
│   │   ├── util-deprecate
│   │   │   ├── browser.js
│   │   │   ├── History.md
│   │   │   ├── LICENSE
│   │   │   ├── node.js
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   └── vite
│   │       ├── bin
│   │       │   ├── openChrome.applescript
│   │       │   └── vite.js
│   │       ├── client.d.ts
│   │       ├── dist
│   │       │   ├── client
│   │       │   │   ├── client.mjs
│   │       │   │   └── env.mjs
│   │       │   ├── node
│   │       │   │   ├── chunks
│   │       │   │   │   ├── dep-BB45zftN.js
│   │       │   │   │   ├── dep-BK3b2jBa.js
│   │       │   │   │   ├── dep-D-7KCb9p.js
│   │       │   │   │   ├── dep-Dnp7gl8U.js
│   │       │   │   │   └── dep-IQS-Za7F.js
│   │       │   │   ├── cli.js
│   │       │   │   ├── constants.js
│   │       │   │   ├── index.d.ts
│   │       │   │   ├── index.js
│   │       │   │   ├── runtime.d.ts
│   │       │   │   ├── runtime.js
│   │       │   │   └── types.d-aGj9QkWt.d.ts
│   │       │   └── node-cjs
│   │       │       └── publicUtils.cjs
│   │       ├── index.cjs
│   │       ├── index.d.cts
│   │       ├── LICENSE.md
│   │       ├── package.json
│   │       ├── README.md
│   │       └── types
│   │           ├── customEvent.d.ts
│   │           ├── hmrPayload.d.ts
│   │           ├── hot.d.ts
│   │           ├── importGlob.d.ts
│   │           ├── import-meta.d.ts
│   │           ├── importMeta.d.ts
│   │           ├── metadata.d.ts
│   │           └── package.json
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── src
│   │   ├── css
│   │   │   └── main.css
│   │   └── js
│   │       ├── main.js
│   │       └── modules
│   │           ├── api
│   │           │   ├── apiService.js
│   │           │   └── config.js
│   │           ├── auth
│   │           │   ├── adminDashboard.js
│   │           │   └── userDashboard.js
│   │           ├── services
│   │           │   ├── chat.js
│   │           │   ├── crops.js
│   │           │   ├── map.js
│   │           │   ├── mlops.js
│   │           │   ├── reports.js
│   │           │   ├── supervisor.js
│   │           │   └── vision.js
│   │           └── ui
│   │               ├── dom.js
│   │               ├── history.js
│   │               ├── i18n.js
│   │               ├── iot.js
│   │               ├── memory.js
│   │               ├── menus.js
│   │               ├── privacy.js
│   │               ├── router.js
│   │               ├── security.js
│   │               └── spinner.js
│   ├── static
│   │   ├── assets
│   │   │   ├── planta.jpeg
│   │   │   └── topo.png
│   │   ├── css
│   │   │   └── styles.css
│   │   ├── img
│   │   │   ├── bugambilia.jpg
│   │   │   ├── cempasuchil.jpg
│   │   │   ├── hongos.jpg
│   │   │   ├── lavanda.jpg
│   │   │   ├── menta.jpg
│   │   │   ├── peyote.jpg
│   │   │   ├── sabila.jpg
│   │   │   └── toronjil.jpg
│   │   ├── js
│   │   │   └── tailwind-compiler.js
│   │   ├── lang
│   │   │   └── es.json
│   │   └── vendor
│   │       ├── chart.min.js
│   │       └── leaflet
│   │           ├── images
│   │           │   ├── layers-2x.png
│   │           │   ├── layers.png
│   │           │   ├── marker-icon-2x.png
│   │           │   ├── marker-icon.png
│   │           │   └── marker-shadow.png
│   │           ├── leaflet.css
│   │           └── leaflet.js
│   ├── staticfiles
│   │   ├── css
│   │   │   └── images
│   │   └── rest_framework
│   │       └── docs
│   │           ├── css
│   │           ├── img
│   │           └── js
│   ├── tailwind.config.js
│   ├── templates
│   │   ├── index.html
│   │   └── requirements_spec.txt
│   └── vite.config.js
├── infrastructure
│   ├── docker-compose.yml
│   ├── mosquitto
│   │   ├── config
│   │   │   └── mosquitto.conf
│   │   ├── data
│   │   │   └── mosquitto.db
│   │   └── log
│   │       └── mosquitto.log
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── render.yaml
├── microservices
│   ├── esp32_node
│   │   ├── include
│   │   │   ├── domain
│   │   │   │   └── TelemetryData.h
│   │   │   └── ports
│   │   │       ├── IComm.h
│   │   │       └── ISensor.h
│   │   ├── lib
│   │   │   ├── comms
│   │   │   │   ├── BleAdapter.h
│   │   │   │   └── WifiMqttAdapter.h
│   │   │   ├── sensors
│   │   │   │   ├── AnalogMoisture.h
│   │   │   │   ├── Dht20Adapter.h
│   │   │   │   └── Ltr390Adapter.h
│   │   │   └── storage
│   │   ├── platformio..ini
│   │   ├── README.md
│   │   └── src
│   │       ├── core
│   │       │   └── TelemetryUseCase.h
│   │       └── main.cpp
│   ├── mole_chat
│   │   ├── app
│   │   │   ├── api
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── main.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── main.cpython-312.pyc
│   │   │   │   │   └── routers.cpython-312.pyc
│   │   │   │   └── routers.py
│   │   │   ├── application
│   │   │   │   ├── ports
│   │   │   │   │   ├── input.py
│   │   │   │   │   └── output.py
│   │   │   │   └── use_cases
│   │   │   │       ├── chat_usecase.py
│   │   │   │       └── __pycache__
│   │   │   │           └── chat_usecase.cpython-312.pyc
│   │   │   ├── core
│   │   │   │   ├── config.py
│   │   │   │   ├── logger.py
│   │   │   │   ├── pii_sanitizer.py
│   │   │   │   └── security.py
│   │   │   ├── domain
│   │   │   │   ├── chat.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── chat.cpython-312.pyc
│   │   │   │   │   ├── exceptions.cpython-312.pyc
│   │   │   │   │   └── schemas.cpython-312.pyc
│   │   │   │   └── schemas.py
│   │   │   └── infrastructure
│   │   │       └── adapters
│   │   │           ├── citation_manager.py
│   │   │           ├── faiss_vector_store.py
│   │   │           ├── llm_client.py
│   │   │           ├── logging_config.py
│   │   │           ├── prompt_loader.py
│   │   │           ├── __pycache__
│   │   │           │   ├── citation_manager.cpython-312.pyc
│   │   │           │   ├── faiss_vector_store.cpython-312.pyc
│   │   │           │   ├── llm_client.cpython-312.pyc
│   │   │           │   ├── prompt_loader.cpython-312.pyc
│   │   │           │   └── redis_sensor_cache_adapter.cpython-312.pyc
│   │   │           └── redis_sensor_cache_adapter.py
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── docs
│   │   │   ├── audit.md
│   │   │   └── requisitos.md
│   │   ├── prompts
│   │   │   └── agronomist.yaml
│   │   ├── requirements.txt
│   │   ├── storage
│   │   │   └── vectors
│   │   └── tests
│   │       ├── test_api_security.py
│   │       ├── test_chat_e2e.py
│   │       ├── test_chat_usecase.py
│   │       ├── test_pii_sanitizer.py
│   │       ├── test_redis_adapter.py
│   │       └── test_upload_pdf.py
│   ├── mole_report
│   │   ├── app
│   │   │   ├── api
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   └── dependencies.cpython-312.pyc
│   │   │   │   └── v1
│   │   │   │       └── reports.py
│   │   │   ├── config.py
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── __pycache__
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── application
│   │   │   ├── __init__.py
│   │   │   ├── services
│   │   │   │   └── report_builder.py
│   │   │   └── use_cases
│   │   │       └── generate_report_use_case.py
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── domain
│   │   │   └── __init__.py
│   │   ├── infrastructure
│   │   │   ├── celery_app.py
│   │   │   ├── db
│   │   │   │   └── supabase_client.py
│   │   │   ├── faiss
│   │   │   │   └── faiss_reader_adapter.py
│   │   │   ├── __init__.py
│   │   │   ├── llm
│   │   │   │   └── huggingface_client.py
│   │   │   ├── pdf
│   │   │   │   └── weasyprint_report_generator.py
│   │   │   ├── redis
│   │   │   │   └── job_metadata_store.py
│   │   │   ├── storage
│   │   │   │   └── s3_adapter.py
│   │   │   └── workers
│   │   │       └── tasks.py
│   │   ├── README.md
│   │   ├── reporte_final.pdf
│   │   ├── requirements.txt
│   │   └── tests
│   │       ├── __init__.py
│   │       └── test_smoke.py
│   └── mole_vision
│       ├── app
│       │   ├── api
│       │   │   ├── dependencies.py
│       │   │   ├── main.py
│       │   │   ├── __pycache__
│       │   │   │   └── main.cpython-312.pyc
│       │   │   └── routers.py
│       │   ├── application
│       │   │   ├── ports
│       │   │   │   ├── event_port.py
│       │   │   │   ├── __init__.py
│       │   │   │   ├── storage_port.py
│       │   │   │   └── vision_port.py
│       │   │   └── use_cases
│       │   │       └── analyze_plant.py
│       │   ├── core
│       │   │   ├── config.py
│       │   │   ├── logger.py
│       │   │   └── security.py
│       │   ├── domain
│       │   │   ├── entities.py
│       │   │   ├── __init__.py
│       │   │   └── schemas.py
│       │   └── infrastructure
│       │       └── adapters
│       │           ├── redis_publisher.py
│       │           ├── supabase_adapter.py
│       │           └── tflite_adapter.py
│       ├── docker-compose.yml
│       ├── Dockerfile
│       ├── docs
│       │   ├── audit.md
│       │   └── requisitos.md
│       ├── models
│       │   ├── labels.json
│       │   └── model.tflite
│       ├── README.md
│       ├── requirements.txt
│       └── tests
│           └── test_vision_api.py
├── pyrightconfig.json
└── README.md
