myApp.factory('pmServ',['$http', function($http){
	return{
		getData : function(fileName){
			var promise = $http({
				method   :  'GET',
			 	url      :  'data/' + fileName
			});
			return promise;
		}
	};
}])