const API_ROOT = "/marauder/api";
const appElement = document.querySelector('[ng-app=app]');

// Native interface (webview to app)
var nativeMock = function () {
  console.warn("Would call native function");
  setTimeout(Client.actionSuccess, 100);
};
var native = window.Native || {
    callPhoneNumber: nativeMock,
    startupCompleted: nativeMock,
  };

// Client interface (app to webview)
var Client = window.Client = {
  actionSuccess: function () {
    var $scope = angular.element(appElement).scope();
    $scope.$apply(function () {
      $scope.actionLoading = false;
    });
  }
};

angular
  .module('app', ['ionic', 'angularMoment'])
  .directive('lastSeen', function () {
    return {
      restrict: 'E',
      replace: true,
      scope: {
        timestamp: "@"
      },
      template: '<span><em ng-if="!timestamp">Jamais vu</em>' +
      '<span ng-if="timestamp">Vu <span am-time-ago="timestamp | amFromUnix | amUtc"></span></span></span>',
    };
  })
  .config(function ($stateProvider, $urlRouterProvider, $ionicConfigProvider) {
    $ionicConfigProvider.tabs.position('bottom');
    $ionicConfigProvider.tabs.style('standard');
    $stateProvider
      .state('tabs', {
        url: "/tab",
        abstract: true,
        templateUrl: "templates/tabs.html",
      })
      .state('tabs.taskforces', {
        url: "/taskforces",
        views: {
          'taskforces-tab': {
            templateUrl: "templates/taskforces.html",
            controller: 'TaskforcesCtrl',
          },
        },
      })
      .state('tabs.map', {
        url: "/map",
        views: {
          'map-tab': {
            templateUrl: "templates/map.html",
            controller: 'MapCtrl',
          },
        },
      });
    $urlRouterProvider.otherwise("/tab/taskforces");
  })
  .factory('api', function ($http) {
    return {
      getTaskForces: function () {
        return $http.get(API_ROOT + '/taskforces/').then(function (response) {
          return response.data;
        });
      },
      getEventSettings: function() {
        return $http.get(API_ROOT + '/event/settings/').then(function(response) {
          return response.data;
        });
      },
      sendUserPing: function (uid, reason) {
        return $http.post(API_ROOT + '/ping/user/', {id: uid, reason: reason}).then(function (response) {
          return response.data;
        });
      },
      sendTaskForcePing: function (tfid, reason) {
        return $http.post(API_ROOT + '/ping/taskforce/', {id: tfid, reason: reason}).then(function (response) {
          return response.data;
        });
      },
    }
  })
  // TODO: directive for abstracting "loading" buttons
  .controller('TaskforcesCtrl', function (api, $rootScope, $scope, $timeout, $ionicPopover, $ionicPopup, $ionicModal) {

    $rootScope.actionLoading = false;
    $scope.shownAccordion = {};
    $scope.ping = {to: null, reason: ''};

    $ionicModal.fromTemplateUrl('templates/ping.html', {
      scope: $scope,
      animation: 'slide-in-up'
    }).then(function (modal) {
      $scope.pingModal = modal;
    });

    $scope.toggleAccordion = function (group, member) {
      if ($scope.isAccordionShown(group, member)) {
        $scope.shownAccordion[group] = null;
      } else {
        $scope.shownAccordion[group] = member;
      }
    };
    $scope.isAccordionShown = function (group, member) {
      return $scope.shownAccordion[group] === member;
    };

    $scope.promptTaskForcePing = function (taskforce) {
      $scope.ping.to = "l'ensemble du groupe " + taskforce.name;
      $scope.ping.send = [api.sendTaskForcePing, taskforce.id];
      $scope.pingModal.show();
    };

    $scope.promptUserPing = function (member) {
      $scope.ping.to = member.fullName;
      $scope.ping.send = [api.sendUserPing, member.id];
      $scope.pingModal.show();
    };

    $scope.sendPing = function () {
      var reason = $scope.ping.reason.trim();
      if (!reason)
        return;
      $scope.ping.reason = '';
      $rootScope.actionLoading = true;
      $scope.pingModal.hide();
      $scope.ping.send[0].call(null, $scope.ping.send[1], reason).then(function () {
        $rootScope.actionLoading = false;
      }, function (err) {
        $ionicPopup.alert({
          title: "Erreur",
          template: "Impossible d'envoyer le ping."
        });
        $rootScope.actionLoading = false;
      });

    };

    $scope.callNumber = function (number) {
      $rootScope.actionLoading = true;
      native.callPhoneNumber(number);
    };

  })
  .controller('MapCtrl', function (api, $rootScope, $scope) {

    var lineStyle = new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: '#fafafa',
        width: 1
      })
    });

    var epitaSource = new ol.source.Vector({
      url: '/static/marauder/epita.geo.json',
      format: new ol.format.GeoJSON()
    });

    var view = new ol.View({
      minZoom: 4,
      maxZoom: 22,
      zoom: 18,
    });

    var map = new ol.Map({
      layers: [
        new ol.layer.Tile({
          source: new ol.source.OSM(),
        }),
        new ol.layer.Vector({
          source: epitaSource,
          style: lineStyle
        }),
      ],
      target: 'map',
      renderer: 'canvas',
      view: view
    });

    map.on('click', function (evt) {
      var lonlat = ol.proj.transform(evt.coordinate, 'EPSG:3857', 'EPSG:4326');
    });

    api.getEventSettings().then(function(settings) {
      view.setCenter(ol.proj.fromLonLat([settings.lon, settings.lat]));
    });

    $scope.$watch('$root.taskForces', function () {
      if (!$rootScope.taskForces)
        return;
      var memberMap = {};
      for (var i = 0; i < $rootScope.taskForces.length; i++) {
        var tf = $rootScope.taskForces[i];
        for (var j = 0; j < tf.members.length; j++) {
          var member = tf.members[j];
          if (member.online && member.location) {
            memberMap[member.id] = member;
          }
        }
      }
      var members = [];
      for (var id in memberMap) {
        if (memberMap.hasOwnProperty(id)) {
          members.push(memberMap[id]);
        }
      }
      $scope.members = members;
      map.getOverlays().forEach(function(overlay) {
        map.removeOverlay(overlay);
      });
      members.map(function(member) {
        var el =  document.getElementById('map-marker-' + member.id);
        if (!el)
          return;
        var overlay = new ol.Overlay({
          element: el,
          positioning: 'center-center',
        });
        overlay.setPosition(ol.proj.transform([member.location.lon, member.location.lat], 'EPSG:4326', 'EPSG:3857'));
        map.addOverlay(overlay);
      });
      map.updateSize();
    });
  })
  .run(function (api, $rootScope, $timeout, $interval, $ionicPopover) {
    function updateTaskForces() {
      api.getTaskForces().then(function (response) {
        $rootScope.taskForces = response;
      });
    }

    // hack to use material icons in tabs (kill me please)
    $timeout(function() {
      $('.tab-title:contains("Task forces")').before($('<i class="icon material-icons">people</i>'));
      $('.tab-title:contains("Map")').before($('<i class="icon material-icons">map</i>'));
    }, 400);

    $ionicPopover.fromTemplateUrl('templates/popover.html', {
      scope: $rootScope,
    }).then(function (popover) {
      $rootScope.popover = popover;
    });

    $rootScope.reloadApp = function () {
      $rootScope.popover.hide();
      window.location.reload();
    };

    $interval(updateTaskForces, 6 * 1000);
    $timeout(updateTaskForces, 1000);

    native.startupCompleted();
  })
;
