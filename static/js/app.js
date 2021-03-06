// Generated by CoffeeScript 1.10.0
(function() {
  var App, Cell, ErrorCell, InputCell, Repl, ResultCell, makeCell, renderExpr,
    extend = function(child, parent) { for (var key in parent) { if (hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    hasProp = {}.hasOwnProperty,
    slice = [].slice;

  makeCell = function(data) {
    var expr, msg;
    switch (data.type) {
      case "expr":
        expr = data.value;
        return new ResultCell(expr);
      case "error":
        console.log(data);
        msg = data.message;
        return new ErrorCell(msg);
      default:
        throw "Invalid result " + result;
    }
  };

  Cell = (function() {
    function Cell() {}

    Cell.prototype.render = function() {
      return $("<div></div>").addClass("cell");
    };

    return Cell;

  })();

  renderExpr = function(s) {
    return _.escape(s);
  };

  InputCell = (function(superClass) {
    extend(InputCell, superClass);

    function InputCell(input1) {
      this.input = input1;
    }

    InputCell.prototype.render = function() {
      var body, elem;
      body = renderExpr(this.input);
      elem = InputCell.__super__.render.call(this).addClass("cell-input").html(body);
      elem.click((function(_this) {
        return function() {
          return $("#input-box").val(_this.input);
        };
      })(this));
      return elem;
    };

    return InputCell;

  })(Cell);

  ResultCell = (function(superClass) {
    extend(ResultCell, superClass);

    function ResultCell(expr1) {
      this.expr = expr1;
    }

    ResultCell.prototype.render = function() {
      var body;
      body = renderExpr(this.expr);
      return ResultCell.__super__.render.call(this).addClass("cell-result").html(body);
    };

    return ResultCell;

  })(Cell);

  ErrorCell = (function(superClass) {
    extend(ErrorCell, superClass);

    function ErrorCell(message) {
      this.message = message;
    }

    ErrorCell.prototype.render = function() {
      var body;
      body = renderExpr(this.message);
      return ErrorCell.__super__.render.call(this).addClass("cell-error").html(body);
    };

    return ErrorCell;

  })(Cell);

  Repl = (function() {
    function Repl() {
      this.exprs = [];
    }

    Repl.prototype.makeUrl = function() {
      var parts;
      parts = 1 <= arguments.length ? slice.call(arguments, 0) : [];
      return parts.join("/");
    };

    Repl.prototype.evalExpr = function(input, inputCb, resultCb) {
      var inputCell, params, url;
      if (resultCb === void 0) {
        resultCb = inputCb;
      }
      url = this.makeUrl("eval");
      params = {
        input: input
      };
      inputCell = new InputCell(input);
      inputCb(inputCell);
      return $.post(url, params, function(res) {
        var resultCell;
        resultCell = makeCell(res);
        return resultCb(resultCell);
      });
    };

    return Repl;

  })();

  App = (function() {
    function App() {
      this.repl = new Repl;
      this.$input = $("#input-box");
      this.$submit = $("#submit-button");
      this.$cells = $("#cell-list");
      this.$submit.click((function(_this) {
        return function() {
          var input;
          input = _this.$input.val().trim();
          _this.$input.val("");
          return _this.repl.evalExpr(input, function(cell) {
            return _this.addCell(cell);
          });
        };
      })(this));
    }

    App.prototype.addCell = function(cell) {
      var elem;
      elem = $("<li></li>");
      elem.append(cell.render());
      return this.$cells.append(elem);
    };

    return App;

  })();

  $(function() {
    $.support.cors = true;
    return window.app = new App;
  });

}).call(this);
