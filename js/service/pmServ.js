myApp.factory('pmServ',['$http', function($http){
	var srv = {};

	return{
		getData : function(fileName){
			var promise = $http({
				method   :  'GET',
			 	url      :  'data/' + fileName
			});
			return promise;
		},

		json2Geojson: function(json){
			var data = {};
			data.type="FeatureCollection";
			data.crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } };
			data.features = [];
			angular.forEach(json,function(value,key){
				var temp = {};
				temp.type = "Feature";
				temp.properties = value;
				temp.geometry = {};
				temp.geometry.type = "Point";
				temp.geometry.coordinates = [value.longitude,value.latitude];
				data.features.push(temp)
			});
			return data;
		},

		json2CityLvl: function(json){
			var data = d3.nest()
						 .key(function(d){return d.area;})
						 .rollup(function(d){return {
							 'aqi':parseInt(d3.sum(d,function(dd){return dd.aqi;})/d.length),
							 'co' :parseInt(d3.sum(d,function(dd){return dd.co;})/d.length),
							 'no2' :parseInt(d3.sum(d,function(dd){return dd.no2;})/d.length),
							 'o3' :parseInt(d3.sum(d,function(dd){return dd.o3;})/d.length),
							 'pm10' :parseInt(d3.sum(d,function(dd){return dd.pm10;})/d.length),
							 'pm2_5' :parseInt(d3.sum(d,function(dd){return dd.pm2_5;})/d.length),
							 'so2' :parseInt(d3.sum(d,function(dd){return dd.so2;})/d.length),
							 'longitude' :d3.sum(d,function(dd){return dd.longitude;})/d.length,
							 'latitude' :d3.sum(d,function(dd){return dd.latitude;})/d.length
					 };})
						 .entries(json);
			var temp = [];
			angular.forEach(data,function(value,key){
				var temp2 = {};
				temp2 = value.values;
				temp2.area = value.key;
				temp.push(temp2);
			});
			return temp;
		},

		colorByAirQuality: function(quality){
			switch(quality){
				case '严重污染':
					return '#360705';
					break;link
				case '重度污染':
					return '#ac1a46';
					break;
				case '中度污染':
					return '#f10505';
					break;
				case '轻度污染':
					return '#9e5c0f';
					break;
				case '良':
					return '#eede0a';
					break;
				case '优':
					return '#37b518';
					break;
				default:
					return 'DarkSlateGray';
					break;
			}
		},

		colorByAqi: function(aqi){
			if(aqi > 300)
					return '#360705';
			else if(aqi > 200)
					return '#ac1a46';
		    else if(aqi > 150)
					return '#f10505';
			else if(aqi > 100)
					return '#9e5c0f';
			else if(aqi > 50)
					return '#eede0a';
			else if(aqi > 0)
					return '#37b518';
			else
					return 'DarkSlateGray';
			},

		getLabel4Path: function(value,isQuality){
			if(!isQuality)
				return value.area;
			else
				return value.position_name + " : " + value.quality;
		},

		showFilter: true

		};

	}])
