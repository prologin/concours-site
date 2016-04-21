const API_ROOT = "/marauder/api";
const appElement = document.querySelector('[ng-app=app]');

// Native interface (webview to app)
var native = window.Native;

// Client interface (app to webview)
var Client = window.Client = {
  actionSuccess: function () {
    var $scope = angular.element(appElement).scope();
    $scope.$apply(function () {
      $scope.actionLoading = false;
    });
  }
};

angular.module('app', ['ionic', 'angularMoment'])
  .factory('webServices', ['$http', function ($http) {
    return {
      getTaskForces: function () {
        return $http.get(API_ROOT + '/taskforces/').then(function (response) {
          return response.data;
        });
      }
      // TODO: other endpoints
    }
  }])
  .directive('lastSeen', function () {
    return {
      restrict: 'E',
      replace: true,
      scope: {
        timestamp: "@"
      },
      template: '<span><em ng-if="!timestamp">Jamais vu</em>' +
      '<span ng-if="timestamp">Vu <span am-time-ago="timestamp | amFromUnix | amUtc"></span></span></span>'
    };
  })
  // TODO: directive for abstracting "loading" buttons
  .controller('MainCtrl', function (webServices, $rootScope, $scope, $timeout, $ionicPopover) {

    $rootScope.actionLoading = false;

    function updateTaskForces(cb) {
      webServices.getTaskForces().then(function (response) {
        $scope.taskForces = response;
        if (cb) cb.call(this, response);
      });
    }

    $ionicPopover.fromTemplateUrl('templates/popover.html', {
      scope: $scope,
    }).then(function (popover) {
      $scope.popover = popover;
    });

    $scope.toggleAccordion = function (member) {
      if ($scope.isAccordionShown(member)) {
        $scope.shownAccordion = null;
      } else {
        $scope.shownAccordion = member;
      }
    };
    $scope.isAccordionShown = function (member) {
      return $scope.shownAccordion === member;
    };

    $scope.doRefresh = function () {
      // the hard way
      // window.location.reload();
      updateTaskForces(function () {
        $scope.$broadcast('scroll.refreshComplete');
      });
    };

    $scope.taskForcePing = function (id) {
      $rootScope.actionLoading = true;
      native.sendTaskForcePing(id);
    };

    $scope.sendPing = function (id) {
      $rootScope.actionLoading = true;
      native.sendPing(id);
    };

    $scope.callNumber = function (number) {
      $rootScope.actionLoading = true;
      native.callPhoneNumber(number);
    };

    native.startupCompleted();
    updateTaskForces();

  });

// Map
/*
var lineStyle = new ol.style.Style({
  stroke: new ol.style.Stroke({
    color: '#fafafa',
    width: 1
  })
});

var vectorSource = new ol.source.Vector({
  url: '/static/marauder/epita.geo.json',
  format: new ol.format.GeoJSON()
});

var view = new ol.View({
  center: ol.proj.fromLonLat([2.3631487758069007, 48.815166921320895]),
  minZoom: 18,
  maxZoom: 22,
  zoom: 18
});

var map = new ol.Map({
  layers: [
    new ol.layer.Vector({
      source: vectorSource,
      style: lineStyle
    })
  ],
  target: 'map',
  renderer: 'canvas',
  view: view
});
*/
