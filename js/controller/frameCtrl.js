myApp.controller('frameCtrl',['$scope', '$rootScope', 'pmServ', function($scope, $rootScope, pmServ){
	$scope.airData = [];
	$scope.stationData = [];

	$scope.count = 0;

	var airPromise = pmServ.getData("air.json");
	airPromise.then(function(result){
		$scope.airData.push(result.data);
		console.log('airData',$scope.airData);

		var stationPromise = pmServ.getData("station.json");
		stationPromise.then(function(result){
			$scope.stationData.push(result.data);
			console.log('stationData',$scope.stationData);
			angular.forEach($scope.airData[0],function(valueAir, keyAir){
				angular.forEach($scope.stationData[0], function(valueStation, keyStation){
					if(valueAir.area==valueStation.area&&valueAir.position_name==valueStation.position_name)
					{
						$scope.count++;
						valueAir.longitude = valueStation.longitude;
						valueAir.latitude = valueStation.latitude;
					}
				})
			});

			console.log('with position', $scope.airData[0], $scope.count);
		});

	});
}])