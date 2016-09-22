angular.module('multirunApp', [])

.controller('mainController', function($scope, $http) {
  $scope.sortPredicate     = 'ID'; // set the default sort type
  $scope.sortReverse  = false;  // set the default sort order
  $scope.searchMultirun   = '';     // set the default search/filter term

  $scope.multiruns = []

  $scope.columns = {
    'id': {
        'name': 'ID',
        'show': true
    },
    'dataset': {
        'name': 'Dataset',
        'show': true
    },
    'state': {
        'name': 'State',
        'show': true
    },
    'bfield': {
        'name': 'BField',
        'show': true
    },
    'cmssw': {
        'name': 'CMSSW',
        'show': true
    },
    'dropbox_log': {
        'name': 'Dropbox log URL',
        'show': true
    },
    'eos_dirs': {
        'name': 'EOS directories',
        'show': true
    },
    'failure_retries': {
        'name': 'Failure Retries',
        'show': true
    },
    'no_payload_retries': {
        'name': 'No payload retries',
        'show': true
    },
    'global_tag': {
        'name': 'Global Tag',
        'show': false
    },
    'number_of_events': {
        'name': 'Events',
        'show': true
    },
    'no_payload_retries': {
        'name': 'No payload retries',
        'show': true
    },
    'perform_payload_upload': {
        'name': 'Payload upload',
        'show': true
    },
    'scram_arch': {
        'name': 'SCRAM architecture',
        'show': false
    },
    'scenario': {
        'name': 'Scenario',
        'show': false
    },
    'run_class_name': {
        'name': 'RunClassName',
        'show': false
    }
  }

  $scope.showColumn = {
        'id': true,
        'dataset': true,
        'state': true
  }

   $scope.getData = function() {
    $http({method: 'GET', url: '/get_multiruns/'})
        .success(function(data, status) {
            $scope.multiruns = data['json_list'];
            console.log($scope.multiruns)
        })
        .error(function(data, status) {
            console.error("Error while loading multiruns");
        })
   }

   $scope.sortBy = function(sortPredicate) {
    $scope.sortReverse = ($scope.sortPredicate === sortPredicate) ? !$scope.sortReverse : false;
    $scope.sortPredicate = sortPredicate;
  };
});