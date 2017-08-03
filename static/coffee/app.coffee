makeCell = (data) ->
    switch data.type
        when "expr"
            expr = data.value
            return new ResultCell expr
        when "error"
            console.log data
            msg = data.message
            return new ErrorCell msg
        else
            throw "Invalid result #{result}"

class Cell
    render: ->
        $("<div></div>").addClass "cell"

renderExpr = (s) ->
    _.escape s

class InputCell extends Cell
    constructor: (@input) ->

    render: ->
        body = renderExpr @input
        elem = super().addClass("cell-input").html body

        elem.click => $("#input-box").val @input
        elem

class ResultCell extends Cell
    constructor: (@expr) ->

    render: ->
        body = renderExpr @expr
        super().addClass("cell-result").html body

class ErrorCell extends Cell
    constructor: (@message) ->

    render: ->
        body = renderExpr @message
        super().addClass("cell-error").html body

############################################################

class Repl
    constructor: () ->
        @exprs = []

    makeUrl: (parts...) ->
        parts.join "/"

    evalExpr: (input, inputCb, resultCb) ->
        if resultCb == undefined
            resultCb = inputCb

        url = this.makeUrl "eval"

        params = {
            input: input
        }

        inputCell = new InputCell input
        inputCb inputCell

        $.post url, params, (res) ->
            resultCell = makeCell res
            resultCb resultCell

############################################################

class App
    constructor: ->
        @repl = new Repl

        this.$input = $("#input-box")
        this.$submit = $("#submit-button")
        this.$cells = $("#cell-list")

        this.$submit.click =>
            input = this.$input.val().trim()
            this.$input.val ""
            @repl.evalExpr input, (cell) => this.addCell cell

    addCell: (cell) ->
        elem = $("<li></li>")
        elem.append cell.render()

        this.$cells.append elem

############################################################

$ ->
    $.support.cors = true
    window.app = new App
