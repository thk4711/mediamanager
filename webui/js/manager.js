//----------------------------------------------------------------------------//
//                      what to do when page is loaded                        //
//----------------------------------------------------------------------------//
$(document).ready(function()
  {
  $('#prev').on('click', function(){
        $.get("/prev", function(data){console.log('prev');});
    });

  $('#playpause').on('click', function(){
        $.get("/toggle", function(data){
          var button_text = $('#playpause').text();
          if ( button_text == 'Play') { $("#playpause").html("Pause"); };
          if ( button_text == 'Pause') { $("#playpause").html("Play"); };
        });
    });

  $('#next').on('click', function(){
        $.get("/next", function(data){console.log('next');});
    });

  $.getJSON('/configdata', function(configdata) {
    start_socket(configdata['web_socket_port']);
    });
  //setInterval(function() {
  //  $.getJSON('/metadata', function(metadata) { update_metadata(metadata); });
  //  }, 1000);
});

//----------------------------------------------------------------------------//
//                      update metadata elments                               //
//----------------------------------------------------------------------------//
function update_metadata(data){
    $("#service").text(data['service']);
    $("#title").text(data['track']);
    $("#artist").text(data['artist']);
    $("#album").text(data['album']);
    $("#cover").attr("src",'/coverimage/' + data['cover']);
    if ( data['playstatus'] == true) { $("#playpause").html("Pause"); };
    if ( data['playstatus'] == false) { $("#playpause").html("Play"); };
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
