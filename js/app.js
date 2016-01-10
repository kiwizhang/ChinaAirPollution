var myApp = angular.module('myApp', [
'ngRoute'
]).
config(['$routeProvider', function($routeProvider){
	$routeProvider.when('/home',{
		templateUrl:'view/homeView.htm',
		controller:''
	});
}]);