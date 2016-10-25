angular.module('multirunApp', ['ngAnimate', 'ngSanitize', 'ui.bootstrap'])

.controller('mainController', function($scope, $http) {

  /* jshint validthis: true */
  var vm = this;

  $scope.sortPredicate     = 'creation_time';
  $scope.sortReverse  = true;  // the 'newest' multirun first
  $scope.searchMultirun   = ''; // display everything

  $scope.multiruns = []
  $scope.multirunsByWorkflow = []
  $scope.splitByWorkflows = false;

//  $scope.currentPage = 1;
  vm.currentPage = 1;
  vm.limit = 25;
  vm.totalItems = 125;

//    #TODO: add totalItems when this works (totalItems can be in particular < limit)
  $scope.tracks = [];

  function getData() {
    $http.get("https://api.spotify.com/v1/search?query=iron+&offset="+($scope.currentPage-1)*$scope.limit+"&limit=20&type=artist")
      .then(function(response) {
        $scope.totalItems = response.data.artists.total
        angular.copy(response.data.artists.items, $scope.tracks)


      });
  }

  vm.pageChanged = function() {
    console.log("Page changed to: " + vm.currentPage);
//    # TODO: what about multiruns by workflow?
    $scope.getMultiruns();
  };

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
    'number_of_events': {
        'name': 'Events',
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

   $scope.getMultiruns = function() {
//   TODO: test if the arithmetic operations are correct and everything works as expected
//    console.log("THIS FUNCTION HAS JUST BEEN INVOKED");
//    console.log("Current Page: " + $scope.currentPage);
//    $http({method: 'GET', url: "/multiruns/?limit=25&offset=0"})
    $http({method: 'GET', url: "/multiruns/?limit="+vm.limit+"&offset="+(vm.currentPage-1)*vm.limit})
        .success(function(data, status) {
            $scope.multiruns = data['multiruns'];
            for (var i = 0; i < $scope.multiruns.length; i++) {
                $scope.multiruns[i]["details"] = false;
                $scope.multiruns[i]["processing_times"] = $scope.parseProcessingTimes($scope.multiruns[i]["processing_times"]);
                $scope.multiruns[i]["creation_time"] = new Date($scope.multiruns[i]["creation_time"]);
            }
            vm.totalItems = data['total'];
            console.log("RECEIVED "+data['multiruns'].length+" ITEMS")
            console.log("TOTAL "+data['total'])
        })
        .error(function(data, status) {
            console.error("Error while loading multiruns");
        })
   }

    $scope.getMultirunsByWorkflow = function() {
    $http({method: 'GET', url: '/multiruns_by_workflow/'})
        .success(function(data, status) {
            $scope.multirunsByWorkflow = data['multiruns'];
            for (var workflow in $scope.multirunsByWorkflow) {
                for (var i = 0; i < $scope.multirunsByWorkflow[workflow].length; i++) {
                    $scope.multirunsByWorkflow[workflow][i]["details"] = false;
                    $scope.multirunsByWorkflow[workflow][i]["processing_times"] = $scope.parseProcessingTimes($scope.multirunsByWorkflow[workflow][i]["processing_times"]);
                    $scope.multirunsByWorkflow[workflow][i]["creation_time"] = new Date($scope.multirunsByWorkflow[workflow][i]["creation_time"]);
                }
            }
        })
        .error(function(data, status) {
            console.error("Error while loading multiruns");
        })
   }

    $scope.switchView = function() {
        $scope.splitByWorkflows = ($scope.splitByWorkflows === true) ? false : true;
    }

   $scope.sortBy = function(sortPredicate) {
    $scope.sortReverse = ($scope.sortPredicate === sortPredicate) ? !$scope.sortReverse : false;
    $scope.sortPredicate = sortPredicate;
  };

    $scope.parseProcessingTimes = function(pt_json){
        // parses list of string dates into Date() objects
        var result = [];
        for (var t = 0; t < pt_json.length; t++){
            var attempt = [];
            var start_time = pt_json[t][0];
            var end_time = pt_json[t][1];
            // end_time can be null, but start_time can't
            attempt.push(new Date(start_time));
            if (end_time == null)
                attempt.push(end_time)
            else
                attempt.push(new Date(end_time));
            result.push(attempt);
        }
        return result;
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