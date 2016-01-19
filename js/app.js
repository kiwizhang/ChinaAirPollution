var myApp = angular.module('myApp', [
'ngRoute',
'leaflet-directive',
'smart-table'
]).
config(['$routeProvider', function($routeProvider){
	$routeProvider
	.when('/home',{
		templateUrl:'view/homeView.htm',
		controller:'homeCtrl'
	})
	.when('/table',{
		templateUrl:'view/tableView.htm',
		controller:'tableCtrl'
	})
}]);
