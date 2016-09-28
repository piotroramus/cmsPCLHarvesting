angular.module('multirunApp', [])

.controller('mainController', function($scope, $http) {
  $scope.sortPredicate     = 'creation_time';
  $scope.sortReverse  = true;  // the 'newest' multirun first
  $scope.searchMultirun   = ''; // display everything

  $scope.multiruns = []

  $scope.columns = {
    'id': {
        'name': 'ID',
        'show': true
    },
    'state': {
        'name': 'State',
        'show': true
    },
    'dataset': {
        'name': 'Dataset',
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
    'perform_payload_upload': {
        'name': 'Payload upload',
        'show': false
    },
    'bfield': {
        'name': 'BField',
        'show': false
    },
    'cmssw': {
        'name': 'CMSSW',
        'show': false
    },
    'dropbox_log': {
        'name': 'Dropbox log URL',
        'show': false
    },
    'eos_dirs': {
        'name': 'EOS directories',
        'show': false
    },
    'global_tag': {
        'name': 'Global Tag',
        'show': false
    },
    'number_of_events': {
        'name': 'Events',
        'show': false
    },
    'no_payload_retries': {
        'name': 'No payload retries',
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
        'name': 'Run Class Name',
        'show': false
    },
    'processing_times': {
        'name': 'Processing Times',
        'show': false
    },
    'runs': {
        'name': 'Runs',
        'show': false
    },
    'creation_time': {
        'name': 'Creation time',
        'show': false
    }
  }

   $scope.getData = function() {
    $http({method: 'GET', url: '/multiruns/'})
        .success(function(data, status) {
            $scope.multiruns = data['json_list'];
            for (var i = 0; i < $scope.multiruns.length; i++) {
                $scope.multiruns[i]["details"] = false;
            }
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

  $scope.stateColors = {
    'Need more data' : "#DCE775",
    'Ready' : "#81D4FA",
    'Processing' : "#80CBC4",
    'Processed OK' : "90CAF9",
    'Processing failed' : "#E57373",
    'DQM upload OK' : "#FFE082",
    'DQM upload failed' : "#CE93D8",
    'Dropbox upload failed' : "#F48FB1",
    'Uploads OK' : "#FFCC80",
  }

  $scope.rowColor = function(state) {
        return {
            "background-color": $scope.stateColors[state]
        };
  }

  $scope.visibleCols = function() {
        // 1 is for the button column which is not in the columns definitions
        var visibleCounter = 1;
        for (var id in $scope.columns){

            if ($scope.columns[id]['show'] === true) visibleCounter++;
        }
        return visibleCounter;
  }
});