var old_volume = 0

//----------------------------------------------------------------------------//
//                      what to do when page is loaded                        //
//----------------------------------------------------------------------------//
$(document).ready(function()
  {
  $('.dropdown-trigger').dropdown({
      closeOnClick: true // Stops event propagation
    });

  $('#prev').on('click', function(){
        $.get("/prev", function(data){});
    });

  $('#service').on('click', function(){
        $.get("/shift", function(data){});
    });

  $('#playpause').on('click', function(){
        $.get("/toggle", function(data){
          var button_text = $('#playpause').text();
          if ( button_text == 'Play') { $("#playpausetext").html("pause"); };
          if ( button_text == 'Pause') { $("#playpausetext").html("pause"); };
        });
    });

  $('#cover').on('click', function(){
        $.get("/toggle", function(data){
          var button_text = $('#playpause').text();
          if ( button_text == 'Play') { $("#playpausetext").html("pause"); };
          if ( button_text == 'Pause') { $("#playpausetext").html("pause"); };
        });
    });

  $('#next').on('click', function(){
        $.get("/next", function(data){});
    });

  $.getJSON('/configdata', function(configdata) {
    start_socket(configdata['web_socket_port']);
    });

  document.addEventListener('swiped-left', function(e) {
    $.get("/next", function(data){});
    });

  document.addEventListener('swiped-right', function(e) {
    $.get("/prev", function(data){});
    });

  create_my_slider();
  slider = document.getElementById('volume');
  slider.noUiSlider.on('change', function(){
    var url = "/volume=" + slider.noUiSlider.get();
    $.get(url, function(data){});
  });
});

//----------------------------------------------------------------------------//
//                    switch active service                                   //
//----------------------------------------------------------------------------//
function switch_service(service){
    var url = '/action=switchservice/service=' + service
    $.get(url, function(data){});
    document.getElementById("active_service").innerHTML = "&nbsp&nbsp&nbsp" + service + "&nbsp&nbsp&nbsp";
    }

//----------------------------------------------------------------------------//
//                      update metadata elments                               //
//----------------------------------------------------------------------------//
function update_metadata(data){
    document.getElementById("active_service").innerHTML = "&nbsp&nbsp&nbsp" + data['service'] + "&nbsp&nbsp&nbsp";
    $("#title").text(data['track']);
    $("#artist").text(data['artist']);
    $("#album").text(data['album']);
    $("#cover").attr("src",'/coverimage/' + data['cover']);
    if ( data['playstatus'] == true) { $("#playpausetext").html("pause"); };
    if ( data['playstatus'] == false) { $("#playpausetext").html("play_arrow"); };
    slider = document.getElementById('volume');
    if (data['volume'] != 0) {
      slider.noUiSlider.set(data['volume']);
      }
    }

//----------------------------------------------------------------------------//
//                   create volume slider                                     //
//----------------------------------------------------------------------------//
function create_my_slider(){
  var slider = document.getElementById('volume');
  noUiSlider.create(slider, {
      start: 0,
      connect: true,
      range: {
          'min': 0,
          'max': 100
        },
      step: 1,
      format: wNumb({
        decimals: 0
        }),
      });
  document.querySelector('.noUi-tooltip').style.background = 'red';
  document.querySelector('.noUi-handle').style.background = 'red';
  }


//----------------------------------------------------------------------------//
//                     start websocket communication                          //
//----------------------------------------------------------------------------//
function start_socket(web_socket_port){
  var ws_url = "ws://" + location.host + ":" + web_socket_port + "/"
  var socket = new WebSocket(ws_url);
  socket.onmessage = function (event) {
    var metadata = JSON.parse(event.data);
    update_metadata(metadata);
    };
  socket.onopen=function(event){
    $.getJSON('/metadata', function(i_metadata) { update_metadata(i_metadata); });
    if(window.timerID){
        window.clearInterval(window.timerID);
        window.timerID=0;
      }
    }
  socket.onclose=function(event){
      if(!window.timerID){
      window.timerID=setInterval(function(){start_socket(web_socket_port)}, 5000);
    }
  }
}
