'use strict';

myApp.controller('tableCtrl',['$scope','$timeout',function($scope,$timeout){

        $scope.airRows = $scope.table.data;

    $('.headerTab').removeClass('active');
    $('.tableTab').addClass('active');

    // $scope.$watch('$parent.zoomA',function(newValue){
    //     $scope.airRows = newValue;
    // })
}]);
