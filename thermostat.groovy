/*
* Nexia Monitored Thermostat
*
* v1 1.13.2016 Initial Build
*/
metadata {
	// Automatically generated. Make future change here.
	definition (name: "Nexia Thermostat v1", namespace: "csdozier", author: "csdozier")
    {
		capability "Refresh"
		capability "Actuator"
		capability "Temperature Measurement"
		capability "Relative Humidity Measurement"
		capability "Thermostat"
		capability "Configuration"
		capability "Polling"
		capability "Sensor"

		command "heatLevelUp"
		command "heatLevelDown"
		command "coolLevelUp"
		command "coolLevelDown"
        command "quickSetCool"
        command "quickSetHeat"
        command "modeoff"
        command "modeheat"
        command "modecool"
        command "modeauto"
        command "fanauto"
        command "fanon"
        command "fancir"
        command "update"

		attribute "thermostatFanState", "string"
        attribute "currentState", "string"
        attribute "currentMode", "string"
        attribute "currentfanMode", "string"
	}
    preferences {
        input("proxy_ip_address", "text", title: "IP", description: "Proxy Server IP Address",defaultValue: "8.8.8.8")
        input("proxy_server_port", "number", title: "Port", description: "Proxy Server Port Number (usually 80 or 443)",defaultValue: 80)
    }
//Thermostat Temp and State
	tiles(scale: 2) {
 		multiAttributeTile(name:"temperature", type: "lighting", width: 6, height: 4){
			tileAttribute ("device.temperature", key: "PRIMARY_CONTROL") {
				attributeState("default", icon:"st.tesla.tesla-hvac", label:'${currentValue}°', unit:"F",
                backgroundColors:[
                    [value: 67, color: "#153591"],
                    [value: 68, color: "#1e9cbb"],
                    [value: 70, color: "#90d2a7"],
                    [value: 74, color: "#44b621"],
                    [value: 76, color: "#f1d801"],
                    [value: 78, color: "#d04e00"],
                    [value: 79, color: "#bc2323"]
                ]
            )
			}
  			tileAttribute("device.humidity", key: "SECONDARY_CONTROL") {
    			attributeState("default", label:'${currentValue}%', unit:"% Humidity")
  			}
		}
		multiAttributeTile(name:"temperatureMulti", type:"thermostat", width:6, height:4) {
  			tileAttribute("device.temperature", key: "PRIMARY_CONTROL") {
    			attributeState("default", label:'${currentValue}°')
                backgroundColors:[
                    [value: 67, color: "#153591"],
                    [value: 68, color: "#1e9cbb"],
                    [value: 70, color: "#90d2a7"],
                    [value: 74, color: "#44b621"],
                    [value: 76, color: "#f1d801"],
                    [value: 78, color: "#d04e00"],
                    [value: 79, color: "#bc2323"]
                ]
  			}
  			tileAttribute("device.temperature", key: "VALUE_CONTROL") {
    			attributeState("default", action: "setTemperature")
  			}
  			tileAttribute("device.humidity", key: "SECONDARY_CONTROL") {
    			attributeState("default", label:'${currentValue}%', unit:"%")
  			}
  			tileAttribute("device.thermostatOperatingState", key: "OPERATING_STATE") {
    			attributeState("default", label:'${currentValue}')
  			}
  			tileAttribute("device.thermostatMode", key: "THERMOSTAT_MODE") {
    			attributeState("default", label:'${currentValue}')
  			}
  			tileAttribute("device.heatingSetpoint", key: "HEATING_SETPOINT") {
    			attributeState("default", label:'${currentValue}')
  			}
  			tileAttribute("device.coolingSetpoint", key: "COOLING_SETPOINT") {
    			attributeState("default", label:'${currentValue}')
  			}
        }
         standardTile("blankTile", "device.temperature", width: 1, height: 1, inactiveLabel: false) {
            state ("default", label:'')
        }
        standardTile("thermostatOperatingState", "device.currentState", canChangeIcon: false, inactiveLabel: false, decoration: "flat", width: 4, height: 1) {
            state ("default", label:'${currentValue}')
        }
		standardTile("thermostatFanState", "device.thermostatFanState", inactiveLabel: false, decoration: "flat", width: 2, height: 2) {
            state "running", label:'Fan is On', icon:"st.Appliances.appliances11"
            state "idle", label:'Fan is Off', icon:"st.Appliances.appliances11"
        }

//Thermostat Mode Control
        standardTile("modeoff", "device.thermostatMode", width: 3, height: 2, inactiveLabel: false, decoration: "flat") {
            state "off", label: '', action:"modeoff", icon:"st.thermostat.heating-cooling-off"
        }
        standardTile("modeheat", "device.thermostatMode", width: 3, height: 2, inactiveLabel: false, decoration: "flat") {
            state "heat", label:'', action:"modeheat", icon:"st.thermostat.heat"
        }
        standardTile("modecool", "device.thermostatMode", width: 3, height: 2, inactiveLabel: false, decoration: "flat") {
            state "cool", label:'', action:"modecool", icon:"st.thermostat.cool"
        }
        standardTile("modeauto", "device.thermostatMode", width: 3, height: 2, inactiveLabel: false, decoration: "flat") {
            state "cool", label:'', action:"modeauto", icon:"st.thermostat.auto"
        }

//Heating Set Point Controls
        standardTile("heatLevelUp", "device.heatingSetpoint", width: 1, height: 1, inactiveLabel: false) {
            state "heatLevelUp", label:'', action:"heatLevelUp", icon:"st.thermostat.thermostat-up", backgroundColor:"#d04e00"
        }
		standardTile("heatLevelDown", "device.heatingSetpoint", width: 1, height: 1, inactiveLabel: false) {
            state "heatLevelDown", label:'', action:"heatLevelDown", icon:"st.thermostat.thermostat-down", backgroundColor:"#d04e00"
        }
        valueTile("heatingSetpoint", "device.heatingSetpoint", width: 2, height: 2, inactiveLabel: false) {
			state "heat", label:'${currentValue}°', unit:"F",
            	backgroundColors:[
					[value: 40, color: "#f49b88"],
					[value: 50, color: "#f28770"],
					[value: 60, color: "#f07358"],
					[value: 70, color: "#ee5f40"],
					[value: 80, color: "#ec4b28"],
					[value: 90, color: "#ea3811"]
				]
		}
		controlTile("heatSliderControl", "device.heatingSetpoint", "slider", height: 2, width: 3, inactiveLabel: false, range:"(60..90)") {
			state "setHeatingSetpoint", action:"quickSetHeat", backgroundColor:"#d04e00"
		}

//Cooling Set Point Controls
        standardTile("coolLevelUp", "device.coolingSetpoint", width: 1, height: 1, inactiveLabel: false) {
            state "coolLevelUp", label:'', action:"coolLevelUp", icon:"st.thermostat.thermostat-up", backgroundColor: "#1e9cbb"
        }
		standardTile("coolLevelDown", "device.coolingSetpoint", width: 1, height: 1, inactiveLabel: false) {
            state "coolLevelDown", label:'', action:"coolLevelDown", icon:"st.thermostat.thermostat-down", backgroundColor: "#1e9cbb"
        }
		valueTile("coolingSetpoint", "device.coolingSetpoint", width: 2, height: 2, inactiveLabel: false) {
			state "cool", label:'${currentValue}°', unit:"F",
            	backgroundColors:[
					[value: 40, color: "#88e1f4"],
					[value: 50, color: "#70dbf2"],
					[value: 60, color: "#58d5f0"],
					[value: 70, color: "#40cfee"],
					[value: 80, color: "#28c9ec"],
					[value: 90, color: "#11c3ea"]
				]
		}
		controlTile("coolSliderControl", "device.coolingSetpoint", "slider", height: 2, width: 3, inactiveLabel: false, range:"(60..90)") {
			state "setCoolingSetpoint", action:"quickSetCool", backgroundColor: "#1e9cbb"
		}

//Fan Mode Control
        standardTile("fanauto", "device.thermostatFanMode", width: 2, height: 2, inactiveLabel: false, decoration: "flat") {
            state "fanauto", label:'', action:"fanauto", icon:"st.thermostat.fan-auto"
        }
        standardTile("fanon", "device.thermostatFanMode", width: 2, height: 2, inactiveLabel: false, decoration: "flat") {
            state "fanon", label:'', action:"fanon", icon:"st.thermostat.fan-on"
        }
        standardTile("fancir", "device.thermostatFanMode", width: 2, height: 2, inactiveLabel: false, decoration: "flat") {
            state "fancir", label:'', action:"fancir", icon:"st.thermostat.fan-circulate"
        }

//Refresh and Config Controls
        standardTile("modefan", "device.currentfanMode", width: 2, height: 2, canChangeIcon: false, inactiveLabel: false, decoration: "flat") {
            state ("default", label:'${currentValue}', icon:"st.Appliances.appliances11")
        }
		standardTile("refresh", "device.thermostatMode", width: 3, height: 2, inactiveLabel: false, decoration: "flat") {
			state "default", action:"polling.poll", icon:"st.secondary.refresh"
		}

        valueTile("statusText", "statusText", inactiveLabel: false, width: 3, height: 2) {
			state "statusText", label:'${currentValue}', backgroundColor:"#ffffff"
		}

// , "heatLevelUp", "coolLevelUp", "heatingSetpoint", "coolingSetpoint", "heatLevelDown", "coolLevelDown"

		main "temperature"
        details(["temperature", "blankTile","thermostatOperatingState","blankTile","heatingSetpoint", "heatLevelUp", "coolLevelUp", "coolingSetpoint", "heatLevelDown", "coolLevelDown", "heatSliderControl", "coolSliderControl", "fanon", "fanauto", "fancir", "modeoff", "modeheat", "modecool", "modeauto", "refresh","temperatureMulti"])
	}
}

def parse(String description)
{
}

private void update(attribute,state) {
    log.debug "update state, request: attribute: ${attribute}  state: ${state}"
    def currentValues = device.currentValue(attribute)
    if(state != currentValues as String) {
    	log.debug "changing state.."
    	sendEvent(name: attribute, value: state)
    }
    if(attribute == "thermostatOperatingState") {
        	log.debug "changing current state.."
    	sendEvent(name: "currentState", value: state)
    }
    }




def updateState(String name, String value) {
	state[name] = value
	device.updateDataValue(name, value)
}



//
//Send commands to the thermostat
//

def heatLevelUp(){
    int nextLevel = device.currentValue("heatingSetpoint") + 1

    if( nextLevel > 90){
    	nextLevel = 90
    }
    log.debug "Setting heat set point up to: ${nextLevel}"
    setHeatingSetpoint(nextLevel)
}

def heatLevelDown(){
    int nextLevel = device.currentValue("heatingSetpoint") - 1

    if( nextLevel < 40){
    	nextLevel = 40
    }
    log.debug "Setting heat set point down to: ${nextLevel}"
    setHeatingSetpoint(nextLevel)
}

def quickSetHeat(degrees) {
	setHeatingSetpoint(degrees)
}

def setHeatingSetpoint(degrees) {
	return request('/heatpoint/set/${degrees}')
}


def coolLevelUp(){
    int nextLevel = device.currentValue("coolingSetpoint") + 1

    if( nextLevel > 99){
    	nextLevel = 99
    }
    log.debug "Setting cool set point up to: ${nextLevel}"
    setCoolingSetpoint(nextLevel)
}

def coolLevelDown(){
    int nextLevel = device.currentValue("coolingSetpoint") - 1

    if( nextLevel < 50){
    	nextLevel = 50
    }
    log.debug "Setting cool set point down to: ${nextLevel}"
    setCoolingSetpoint(nextLevel)
}

def quickSetCool(degrees) {
	setCoolingSetpoint(degrees)
}

def setCoolingSetpoint(degrees) {
	return request('/coolpoint/set/${degrees}')
}

def modeoff() {
	log.debug "Setting thermostat mode to OFF."

	return request('/mode/set/OFF')

}

def modeheat() {
	log.debug "Setting thermostat mode to HEAT."
	return request('/mode/set/HEAT')
}

def modecool() {
	log.debug "Setting thermostat mode to COOL."
	return request('/mode/set/COOL')

}

def modeauto() {
	log.debug "Setting thermostat mode to AUTO."
	return request('/mode/set/AUTO')

}

def modeemgcyheat() {
	return request('/mode/set/emergencyheat')

}
def fanon() {
	log.debug "Setting fan mode to ON."
	return request('/fanmode/set/on')

}

def fanauto() {
	log.debug "Setting fan mode to AUTO."
	return request('/fanmode/set/auto')
}

def fancir() {
	log.debug "Setting fan mode to CIRCULATE."
	return request('/fanmode/set/circulate')
}

def poll() {
	return request('/refresh')
}

def configure() {
}

private getStandardDelay() {
	1000
}

def request(request) {
	log.debug("Request:'${request}'")
    def hosthex = convertIPtoHex(proxy_ip_address)
    def porthex = convertPortToHex(proxy_server_port)
    log.debug("${device.deviceNetworkId}")
    def hubAction = new physicalgraph.device.HubAction(
   	 		'method': 'GET',
    		'path': "/nexiatherm${request}"+"&apiserverurl="+java.net.URLEncoder.encode(apiServerUrl("/api/smartapps/installations"), "UTF-8"),
        	'body': '',
        	'headers': [ HOST: "${hosthex}:${porthex}" ]
		)

    log.debug hubAction
    return hubAction
}


private String convertIPtoHex(ipAddress) {
	log.debug('convertIPtoHex:'+"${ipAddress}")
    String hex = ipAddress.tokenize( '.' ).collect {  String.format( '%02X', it.toInteger() ) }.join()
    return hex
}

private String convertPortToHex(port) {
	log.debug('convertIPtoHex:'+"${port}")
	String hexport = port.toString().format( '%04X', port.toInteger() )
    return hexport
}
