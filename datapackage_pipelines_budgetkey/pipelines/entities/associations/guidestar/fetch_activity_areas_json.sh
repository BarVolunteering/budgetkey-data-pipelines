#!/bin/sh

curl 'http://www.guidestar.org.il/apexremote' -H 'Cookie: has_js=1' -H 'X-User-Agent: Visualforce-Remoting' -H 'Origin: http://www.guidestar.org.il' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: en-US,en;q=0.9,he;q=0.8' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36' -H 'Content-Type: application/json' -H 'Accept: */*' -H 'Referer: http://www.guidestar.org.il/GS_AdvancedSearchForm' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --data-binary '{"action":"GS_AdvancedSearchController","method":"getClassifications","data":null,"type":"rpc","tid":2,"ctx":{"csrf":"VmpFPSxNakF4T0Mwd05DMHhNMVF3TnpvMU16b3lOaTR5TkRGYSxyWk4waExQQ09WeTJJNnVPMWJuV3IzLFpXWTNaRFkz","vid":"06624000003srHx","ns":"","ver":31}}' --compressed | json_pp -json_opt canonical,pretty > activity_areas.json