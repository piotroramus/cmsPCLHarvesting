angular.module('multirunApp', [])

.controller('basicController', function($scope, $http) {
  $scope.sortType     = 'id'; // set the default sort type
  $scope.sortReverse  = false;  // set the default sort order
  $scope.searchMultirun   = '';     // set the default search/filter term

  $scope.multiruns = []

  $scope.showColumn = {
        'id': true,
        'dataset': true,
        'state': true
  }

   $scope.getData = function() {
    $http({method: 'GET', url: '/multiruns/'})
        .success(function(data, status) {
            $scope.multiruns = data['multiruns'];
            console.log($scope.multiruns)
        })
        .error(function(data, status) {
            console.error("Error while loading multiruns");
        })
   }
});