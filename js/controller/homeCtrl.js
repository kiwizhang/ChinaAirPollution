'use strict';

myApp.controller('homeCtrl',['$scope',function($scope){

    $scope.$parent.showFilter = true;
    $('.headerTab').removeClass('active');
    $('.homeTab').addClass('active');

}]);
