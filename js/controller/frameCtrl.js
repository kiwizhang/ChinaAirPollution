myApp.controller('frameCtrl',['$scope', '$rootScope', '$timeout', 'leafletData', 'pmServ', function($scope, $rootScope, $timeout, leafletData, pmServ){
	$scope.airData = [];
	$scope.zoomA = null;
	$scope.zoomB = null;
	$scope.stationData = [];
	$scope.airGeojson = null;
	$scope.display = null;
	$scope.zoomSkip = 7;
	$scope.paths = {};
	$scope.pathClicked = null;
	$scope.popUpVisible = false;
	$scope.popUpPosition = {};
	$scope.table = {};
	$scope.table.data = null;
	$scope.airOptions = [
		{'name':'aqi','title':'AQI'},
		{'name':'co','title':'CO'},
		//{'name':'co_24h'},
		{'name':'no2','title':'NO2'},
		//{'name':'no2_24h'},
		{'name':'o3','title':'O3'},
		//{'name':'o3_8h'},
		{'name':'pm10','title':'PM10'},
		//{'name':'pm10_24h'},
		{'name':'pm2_5','title':'PM2.5'},
		//{'name':'pm2_5_24h'},
		{'name':'so2','title':'SO2'}
		//{'name':'so2_24h'},
	];

	$scope.showFilter = pmServ.showFilter;

	$scope.optionSelected = $scope.airOptions[0];

	angular.extend($scope,{
		China:{
			lat : 38.460669951495305,
			lng : 105.28125,
			zoom: 4
		},

		defaults:{
			//tileLayer: "http://{s}.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
            zoomControlPosition: 'topright',
            tileLayerOptions: {
                opacity: 0.9,
                detectRetina: true,
                reuseTiles: true,
            }
		},

		maxbounds: {
			northEast: {
				lat: 48,
				lng: 140
			},
			southWest: {
				lat: 22,
				lng: 70
			}
		},

	    tiles: {
	        url: "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
	    },

        legend: {
            position: 'bottomleft',
            colors: [ '#360705', '#ac1a46', '#f10505', '#9e5c0f','#eede0a',"#37b518"],
            labels: [ "严重污染", "重度污染", "中度污染", "轻度污染", "良", "优"]
        },

		events: {
			path: {
				enable:['click','mouseover']
			}
		},

		controls: {}
	});


	leafletData.getMap().then(function(){
		angular.extend($scope.controls,{
			minimap: {
				type: 'minimap',
				layer: {
					name: 'OpenStreetMap',
					url: 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
					type: 'xyz'
				},
				toggleDisplay: true
			}
		});
	})


	$scope.$on('leafletDirectivePath.click',function(event,path){
		$scope.pathClicked = $scope.paths[path.modelName].data;
		if($scope.China.zoom < $scope.zoomSkip){
			$scope.China.lat = $scope.pathClicked.latitude;
			$scope.China.lng = $scope.pathClicked.longitude;
			$scope.China.zoom = 10;
		}
	})

	// $scope.$on('leafletDirectivePath.mouseover',function(event,path){
	// 	$scope.paths[path.modelName].label={message:'no fuck'};
	//
	// })

    $scope.$watch("China.zoom", function(zoom) {
        $scope.tiles.url = (zoom < $scope.zoomSkip)
                ? "http://{s}.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png"
                : "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

		// if(zoomOld < $scope.zoomSkip && zoom > ($scope.zoomSkip-1))
		// 	$scope.pathClicked = null;
		//
		// if(zoomOld > ($scope.zoomSkip-1) && zoom < $scope.zoomSkip)
		// 	$scope.pathClicked = null;

		if(zoom < $scope.zoomSkip){
			console.log('zoom false');
			$scope.display = $scope.zoomB;
			$scope.paths = {};
			angular.forEach($scope.display,function(value,key){
				$scope.paths['circle'+key] = {
					type : 'circle',
					fillColor : pmServ.colorByAqi(value.aqi),
					color     : '#000000',
					weight    : 0,
					opacity   : 1,
					fillOpacity : 0.8,
					stroke : false,
					clickable : true,
					data 	  : value,
					latlngs : [value.latitude,value.longitude],
					//label : {message : 'fuck'},
					radius : (value[$scope.optionSelected.name]==null||value[$scope.optionSelected.name]==0)?0.0000001:Math.sqrt(value[$scope.optionSelected.name])*3000
				};
			});
		}
		else {
			console.log('zoom true');
			$scope.display = $scope.zoomA;
			$scope.paths = {};
			angular.forEach($scope.display,function(value,key){
				$scope.paths['circle'+key] = {
					type : 'circle',
					fillColor : pmServ.colorByAirQuality(value.quality),
					color     : '#000000',
					weight    : 0,
					opacity   : 1,
					fillOpacity : 0.8,
					stroke : false,
					clickable : true,
					data 	  : value,
					latlngs : [value.latitude,value.longitude],
					//label : {message : 'no fuck'},
					radius : (value[$scope.optionSelected.name]==null||value[$scope.optionSelected.name]==0)?0.0000001:Math.sqrt(value[$scope.optionSelected.name])*160
				};
			});
		}
    });

	var airPromise = pmServ.getData("air.json");
	airPromise.then(function(result){
		$scope.airData.push(result.data);

		var stationPromise = pmServ.getData("station.json");
		stationPromise.then(function(result){
			$scope.stationData.push(result.data);
			angular.forEach($scope.airData[0],function(valueAir, keyAir){
				angular.forEach($scope.stationData[0], function(valueStation, keyStation){
					if(valueAir.area==valueStation.area&&valueAir.position_name==valueStation.position_name)
					{
						valueAir.longitude = valueStation.longitude;
						valueAir.latitude = valueStation.latitude;
					}
				});
			});

			var temp = [];
			angular.forEach($scope.airData[0],function(value,key){
				if(!(angular.isUndefined(value.longitude)||angular.isUndefined(value.latitude)||isNaN(value.longitude)||isNaN(value.latitude)))
					temp.push(value);
			});
			$scope.airData[0]=temp;
			$scope.table.data = temp;

			$scope.zoomB = pmServ.json2CityLvl($scope.airData[0]);
			$scope.zoomA = $scope.airData[0];
			$scope.display = $scope.zoomB;

			$scope.paths = {};
			angular.forEach($scope.display,function(value,key){
				$scope.paths['circle'+key] = {
					type : 'circle',
					fillColor : pmServ.colorByAqi(value.aqi),
					color     : '#000000',
					weight    : 0,
					opacity   : 1,
					fillOpacity : 0.8,
					stroke : false,
					clickable : true,
					data 	  : value,
					latlngs : [value.latitude,value.longitude],
					//label : {message : 'fuck'},
					radius : (value[$scope.optionSelected.name]==null||value[$scope.optionSelected.name]==0)?0.0000001:Math.sqrt(value[$scope.optionSelected.name])*3000
				};
			});

			$scope.$watch('optionSelected',function(newValue){
				$scope.paths = {};
				if($scope.China.zoom < $scope.zoomSkip){
					angular.forEach($scope.display,function(value,key){
						$scope.paths['circle'+key] = {
							type : 'circle',
							fillColor : pmServ.colorByAqi(value.aqi),
							color     : '#000000',
							weight    : 0,
							opacity   : 1,
							fillOpacity : 0.8,
							stroke : false,
							clickable : true,
							data 	  : value,
							latlngs : [value.latitude,value.longitude],
							//label : {message : 'fuck'},
							radius : (value[newValue.name]==null||value[newValue.name]==0)?0.0000001:Math.sqrt(value[newValue.name])*3000
						};
					});
				}
				else{
					angular.forEach($scope.display,function(value,key){
						$scope.paths['circle'+key] = {
							type : 'circle',
							fillColor : pmServ.colorByAirQuality(value.quality),
							color     : '#000000',
							weight    : 0,
							opacity   : 1,
							fillOpacity : 0.8,
							stroke : false,
							clickable : true,
							data 	  : value,
							latlngs : [value.latitude,value.longitude],
							//label : {message : 'no fuck'},
							radius : (value[newValue.name]==null||value[newValue.name]==0)?0.0000001:Math.sqrt(value[newValue.name])*160
						};
					});
				}
			})

			// $scope.$watch('display',function(newValue){
			// 	console.log('display value',newValue);
			// 	if($scope.China.zoom < $scope.zoomSkip){
			// 		$scope.paths = {};
			// 		angular.forEach(newValue,function(value,key){
			// 			$scope.paths['circle'+key] = {
			// 				type : 'circle',
			// 				fillColor : pmServ.colorByAqi(value.aqi),
			// 				color     : '#000000',
			// 				weight    : 0,
			// 				opacity   : 1,
			// 				fillOpacity : 0.8,
			// 				stroke : false,
			// 				clickable : true,
			// 				data 	  : value,
			// 				latlngs : [value.latitude,value.longitude],
			// 				label : {message : 'fuck'},
			// 				radius : (value[$scope.optionSelected.name]==null||value[$scope.optionSelected.name]==0)?0.0000001:Math.sqrt(value[$scope.optionSelected.name])*3000
			// 			};
			// 		});
			// 	}
			// 	else{
			// 		$scope.paths = {};
			// 		angular.forEach(newValue,function(value,key){
			// 			$scope.paths['circle'+key] = {
			// 				type : 'circle',
			// 				fillColor : pmServ.colorByAirQuality(value.quality),
			// 				color     : '#000000',
			// 				weight    : 0,
			// 				opacity   : 1,
			// 				fillOpacity : 0.8,
			// 				stroke : false,
			// 				clickable : true,
			// 				data 	  : value,
			// 				latlngs : [value.latitude,value.longitude],
			// 				label : {message : 'no fuck'},
			// 				radius : (value[$scope.optionSelected.name]==null||value[$scope.optionSelected.name]==0)?0.0000001:Math.sqrt(value[$scope.optionSelected.name])*160
			// 			};
			// 		});
			// 	}
			// })
		});

	});
}])
